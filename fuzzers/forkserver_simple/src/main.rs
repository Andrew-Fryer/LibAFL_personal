use core::time::Duration;
use std::{path::PathBuf, str::FromStr};
use time::OffsetDateTime;

use clap::{self, Parser};
use libafl::{
    bolts::{
        current_nanos,
        rands::StdRand,
        shmem::{ShMem, ShMemProvider, UnixShMemProvider},
        tuples::{tuple_list, MatchName, Merge},
        AsMutSlice,
    },
    corpus::{Corpus, InMemoryCorpus, OnDiskCorpus},
    events::SimpleEventManager,
    executors::{
        forkserver::{ForkserverExecutor, TimeoutForkserverExecutor},
        HasObservers,
    },
    feedback_and_fast, feedback_or,
    feedbacks::{CrashFeedback, MaxMapFeedback, TimeFeedback},
    fuzzer::{Fuzzer, StdFuzzer},
    inputs::BytesInput,
    monitors::SimpleMonitor,
    mutators::{scheduled::havoc_mutations, tokens_mutations, StdScheduledMutator, Tokens},
    observers::{HitcountsMapObserver, MapObserver, StdMapObserver, TimeObserver},
    schedulers::{IndexesLenTimeMinimizerScheduler, QueueScheduler},
    stages::mutational::StdMutationalStage,
    state::{HasCorpus, HasMetadata, StdState}, prelude::{CoverageMonitor, ConstFeedback, forkserver, OutputFeedback, InputFeedback, OutputObserver, Feedback, HasClientPerfMonitor, UsesInput, CombinedFeedback, MapFeedback, DifferentIsNovel, MaxReducer, RomuDuoJrRand, LogicEagerOr, InputObserver}, feedback_and,
};
use nix::sys::signal::Signal;

/// The commandline args this fuzzer accepts
#[derive(Debug, Parser)]
#[command(
    name = "forkserver_simple",
    about = "This is a simple example fuzzer to fuzz a executable instrumented by afl-cc.",
    author = "tokatoka <tokazerkje@outlook.com>"
)]
struct Opt {
    #[arg(
        help = "The instrumented binary we want to fuzz",
        name = "EXEC",
        default_value = "./knotd_stdio"
        // default_value = "./target/release/program"
    )]
    executable: String,

    #[arg(
        help = "The directory to read initial inputs from ('seeds')",
        name = "INPUT_DIR",
        default_value = "./corpus"
    )]
    in_dir: PathBuf,

    #[arg(
        help = "Timeout for each individual execution, in milliseconds",
        short = 't',
        long = "timeout",
        default_value = "10000"
    )]
    timeout: u64,

    #[arg(
        help = "If not set, the child's stdout and stderror will be redirected to /dev/null",
        short = 'd',
        long = "debug-child",
        default_value = "true"
        // default_value = "false"
    )]
    debug_child: bool,

    #[arg(
        help = "Arguments passed to the target",
        name = "arguments",
        num_args(1..),
        allow_hyphen_values = true,
    )]
    arguments: Vec<String>,

    #[arg(
        help = "Signal used to stop child",
        short = 's',
        long = "signal",
        value_parser = str::parse::<Signal>,
        default_value = "SIGKILL"
    )]
    signal: Signal,
}

#[allow(clippy::similar_names)]
pub fn main() {
    const MAP_SIZE: usize = 65536;

    let opt = Opt::parse();

    let corpus_dirs: Vec<PathBuf> = [opt.in_dir].to_vec();

    // The unix shmem provider supported by AFL++ for shared memory
    let mut shmem_provider = UnixShMemProvider::new().unwrap();

    // The coverage map shared between observer and executor
    let mut shmem = shmem_provider.new_shmem(MAP_SIZE).unwrap();
    // let the forkserver know the shmid
    shmem.write_to_env("__AFL_SHM_ID").unwrap();
    let shmem_buf = shmem.as_mut_slice();

    // Create an observation channel using the signals map
    let edges_observer = HitcountsMapObserver::new(StdMapObserver::new("shared_mem", shmem_buf));

    // Create an observation channel to keep track of the execution time
    let time_observer = TimeObserver::new("time");

    let input_observer = InputObserver::new("input");
    let output_observer = OutputObserver::new("output");

    // Feedback to rate the interestingness of an input
    // This one is composed by two Feedbacks in OR
    #[cfg(feedback_alg = "AflEdges")]
    let (feedback_name, mut feedback) = (&"AflEdges", feedback_or!(
        // New maximization map feedback linked to the edges observer and the feedback state
        MaxMapFeedback::new_tracking(&edges_observer, true, false),
        // Time feedback, this one does not need a feedback state
        TimeFeedback::new_with_observer(&time_observer)
    ));
    // TODO: I should probably change this to probabilistically pick inputs because this logs every exec and keeps all inputs in the corpus in memory (I think), which is probably pretty bad for performance...
    #[cfg(feedback_alg = "ConstTrue")]
    let (feedback_name, mut feedback) = (&"ConstTrue", feedback_or!(
        // New maximization map feedback linked to the edges observer and the feedback state
        MaxMapFeedback::new_tracking(&edges_observer, true, false),
        ConstFeedback::True,
        // Time feedback, this one does not need a feedback state
        TimeFeedback::new_with_observer(&time_observer)
    ));
    #[cfg(feedback_alg = "GrammarInput")]
    let (feedback_name, mut feedback) = (&"GrammarInput", feedback_or!(
        // New maximization map feedback linked to the edges observer and the feedback state
        feedback_and!(
            MaxMapFeedback::new_tracking(&edges_observer, true, false),
            ConstFeedback::False // this ensures that MaxMapFeedback doesn't help us out
        ),
        InputFeedback::new_with_observer(&input_observer),
        // Time feedback, this one does not need a feedback state
        TimeFeedback::new_with_observer(&time_observer)
    ));
    #[cfg(feedback_alg = "GrammarOutput")]
    let (feedback_name, mut feedback) = (&"GrammarOutput", feedback_or!(
        // New maximization map feedback linked to the edges observer and the feedback state
        feedback_and!(
            MaxMapFeedback::new_tracking(&edges_observer, true, false),
            ConstFeedback::False // this ensures that MaxMapFeedback doesn't help us out
        ),
        OutputFeedback::new_with_observer(&output_observer),
        // Time feedback, this one does not need a feedback state
        TimeFeedback::new_with_observer(&time_observer)
    ));
    #[cfg(feedback_alg = "GrammarFull")]
    let (feedback_name, mut feedback) = (&"GrammarFull", feedback_or!(
        // New maximization map feedback linked to the edges observer and the feedback state
        feedback_and!(
            MaxMapFeedback::new_tracking(&edges_observer, true, false),
            ConstFeedback::False // this ensures that MaxMapFeedback doesn't help us out
        ),
        InputFeedback::new_with_observer(&input_observer),
        OutputFeedback::new_with_observer(&output_observer),
        // Time feedback, this one does not need a feedback state
        TimeFeedback::new_with_observer(&time_observer)
    ));

    // A feedback to choose if an input is a solution or not
    // We want to do the same crash deduplication that AFL does
    let mut objective = feedback_and_fast!(
        // Must be a crash
        CrashFeedback::new(),
        // Take it only if trigger new coverage over crashes
        MaxMapFeedback::new(&edges_observer)
    );

    // create a State from scratch
    let mut state = StdState::new(
        // RNG
        StdRand::with_seed(current_nanos()),
        // Corpus that will be evolved, we keep it in memory for performance
        InMemoryCorpus::<BytesInput>::new(),
        // Corpus in which we store solutions (crashes in this example),
        // on disk so the user can get them after stopping the fuzzer
        OnDiskCorpus::new(PathBuf::from("./crashes")).unwrap(),
        // States of the feedbacks.
        // The feedbacks can report the data that should persist in the State.
        &mut feedback,
        // Same for objective feedbacks
        &mut objective,
    )
    .unwrap();

    // The Monitor trait define how the fuzzer stats are reported to the user
    let timestamp = OffsetDateTime::now_utc();
    let coverage_file = format!("./coverage_logs/coverage_{:?}_{}.csv", feedback_name, timestamp);
    let monitor = CoverageMonitor::new(|s| println!("{}", s), &coverage_file).expect("successfully created CoverageMonitor");

    // The event manager handle the various events generated during the fuzzing loop
    // such as the notification of the addition of a new item to the corpus
    let mut mgr = SimpleEventManager::new(monitor);

    // A minimization+queue policy to get testcasess from the corpus
    // let scheduler = IndexesLenTimeMinimizerScheduler::new(QueueScheduler::new());
    let scheduler = QueueScheduler::new();

    // A fuzzer with feedbacks and a corpus scheduler
    let mut fuzzer = StdFuzzer::new(scheduler, feedback, objective);

    // If we should debug the child
    let debug_child = opt.debug_child;

    // Create the executor for the forkserver
    let args = opt.arguments;

    let mut tokens = Tokens::new(); // TODO: try removing this! (andrew)
    let mut forkserver = ForkserverExecutor::builder()
        .program(opt.executable)
        .debug_child(debug_child)
        .shmem_provider(&mut shmem_provider)
        .autotokens(&mut tokens)
        .parse_afl_cmdline(args)
        .coverage_map_size(MAP_SIZE)
        .is_persistent(true)
        .pipe_input(true)
        // .build(tuple_list!(time_observer, edges_observer))
        .build(tuple_list!(time_observer, edges_observer, input_observer, output_observer))
        // .build(tuple_list!(time_observer, edges_observer, output_observer))
        .unwrap();

    if let Some(dynamic_map_size) = forkserver.coverage_map_size() {
        forkserver
            .observers_mut()
            .match_name_mut::<HitcountsMapObserver<StdMapObserver<'_, u8, false>>>("shared_mem")
            .unwrap()
            .downsize_map(dynamic_map_size);
    }

    let forkserver_input_pipe = forkserver.input_pipe();
    let mut executor = TimeoutForkserverExecutor::with_signal(
        forkserver,
        Duration::from_millis(opt.timeout),
        opt.signal,
        true,
        forkserver_input_pipe,
    )
    .expect("Failed to create the executor.");

    // In case the corpus is empty (on first run), reset
    if state.corpus().count() < 1 {
        state
            .load_initial_inputs(&mut fuzzer, &mut executor, &mut mgr, &corpus_dirs)
            .unwrap_or_else(|err| {
                panic!(
                    "Failed to load initial corpus at {:?}: {:?}",
                    &corpus_dirs, err
                )
            });
        println!("We imported {} inputs from disk.", state.corpus().count());
    }

    state.add_metadata(tokens);

    // Setup a mutational stage with a basic bytes mutator
    let mutator =
        StdScheduledMutator::with_max_stack_pow(havoc_mutations().merge(tokens_mutations()), 6);
    let mut stages = tuple_list!(StdMutationalStage::new(mutator));

    let iters = 20000; // TODO: why isn't it stopping at 100000 execs?
    fuzzer
        .fuzz_loop_for(&mut stages, &mut executor, &mut state, &mut mgr, iters)
        // .fuzz_loop(&mut stages, &mut executor, &mut state, &mut mgr)
        .expect("Error in the fuzzing loop");
}
