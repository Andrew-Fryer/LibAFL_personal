for feedback_alg in "AflEdges" "ConstTrue" "GrammarInput" "GrammarOutput" "GrammarFull"; do
    cargo +1.70.0 rustc --release -- --cfg feedback_alg=\""${feedback_alg}"\"
    for i in {1..10}; do
        ./target/release/forkserver_simple
    done
done
