from matplotlib import pyplot as plt
import pandas as pd
import glob
from statistics import mean, stdev


coverage_log_dirs = [
    "coverage_logs",
    "coverage_logs_run_1",
    "coverage_logs_run_2",
]

# afl_edges_files = glob.glob('coverage_"AflEdges"_*.csv')
# const_true_files = glob.glob('coverage_"ConstTrue"_*.csv')

coverage_at_end = {}

columns = ["num_execs", "coverage", "map_size"]
def plot_files(feedback_type, color):
    for coverage_log_dir in coverage_log_dirs:
        path = './{}/coverage_"{}"_*.csv'.format(coverage_log_dir, feedback_type)
        files = glob.glob(path)
        coverage_at_end[feedback_type] = []
        for f in files:
            df = pd.read_csv(f, names=columns)
            # plt.plot(df.num_execs, df.coverage, label=feedback_type)
            plt.plot(df.num_execs, df.coverage, color=color, linewidth=0.5)
            # plt.scatter(df.num_execs, df.coverage, color=color)
            coverage_at_end[feedback_type].append(df.coverage.iloc[-1])

plot_files("AflEdges", "red")
plot_files("ConstTrue", "blue")
plot_files("GrammarInput", "orange")
plot_files("GrammarOutput", "yellow")
plot_files("GrammarFull", "purple")
plt.xlabel("Num Execs")
plt.ylabel("Coverage")
# plt.legend()
plt.savefig("coverage_plot.png")

stats = {}
for feedback_type in coverage_at_end:
    vals = coverage_at_end[feedback_type]
    if len(vals) > 0:
        m = mean(vals)
        s = stdev(vals)
        stats[feedback_type] = {
            "mean": m,
            "stdev": s,
            "min_dev": m - 2 * s,
            "max_dev": m + 2 * s,
        }
        # print(feedback_type, mean(vals), stdev(vals))
    # plt.scatter(vals)
# print(stats)
for feedback_type in stats:
    print(feedback_type, stats[feedback_type])
