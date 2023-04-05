from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import glob
from statistics import mean, stdev


coverage_log_dirs = [
    "coverage_logs",
    "coverage_logs_run_1",
    "coverage_logs_run_2",
]

feedback_types = [
    ("AflEdges", "red"),
    ("ConstTrue", "blue"),
    ("GrammarInput", "orange"),
    ("GrammarOutput", "yellow"),
    ("GrammarFull", "purple"),
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
            final_coverage_value = df.coverage.iloc[-1]
            coverage_at_end[feedback_type].append(final_coverage_value)

for ft, c in feedback_types:
    plot_files(ft, c)
plt.xlabel("Num Execs")
plt.ylabel("Coverage")
# plt.legend()
plt.savefig("coverage_plot.png")
plt.clf()

stats = {}
hist_vals = []
colors = []
labels = []
fig, axs = plt.subplots(len(feedback_types))
i = 0
x_start = 800
x_end = 1300
bins = np.linspace(x_start, x_end, 50)
for feedback_type, c in feedback_types:
    vals = coverage_at_end[feedback_type]
    if len(vals) > 0:
        m = mean(vals)
        s = stdev(vals)
        stats[feedback_type] = {
            "mean": m,
            "stdev": s,
            "min_dev": m - 2 * s,
            "max_dev": m + 2 * s,
            "num_vals": len(vals),
        }
        # print(feedback_type, mean(vals), stdev(vals))
    hist_val, _bins = np.histogram(vals, bins)
    hist_vals.append(vals)
    # hist_vals.append(hist_val)
    colors.append(c)
    labels.append(feedback_type)

    h, edges = np.histogram(vals, bins=bins)

    axs[i].stairs(h, bins, color=c, label=feedback_type)
    axs[i].set_xlim(x_start, x_end)
    axs[i].set_ylim(0, 6)
    axs[i].legend()
    i += 1
plt.savefig("coverage_hist.png")

# print(stats)
for feedback_type in stats:
    print(feedback_type, stats[feedback_type])
