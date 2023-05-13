from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import glob
from statistics import mean, stdev
import math
import scipy


coverage_log_dirs = [
    # "coverage_logs",
    "coverage_logs_run_1",
    "coverage_logs_run_2",
    "coverage_logs_run_3",
    "coverage_logs_run_4",
    "coverage_logs_run_5",
    "coverage_logs_run_6",
    "coverage_logs_run_7",
    "coverage_logs_run_8",
    "coverage_logs_run_9",
    "coverage_logs_run_10",
]

feedback_types = [
    ("AflEdges", "red"),
    ("GrammarFull", "purple"),
    ("GrammarInput", "orange"),
    ("GrammarOutput", "yellow"),
    ("ConstTrue", "blue"),
]

coverage_at_end = {}

columns = ["num_execs", "coverage", "map_size"]
def plot_files(feedback_type, color):
    for coverage_log_dir in coverage_log_dirs:
        path = './{}/coverage_"{}"_*.csv'.format(coverage_log_dir, feedback_type)
        files = glob.glob(path)
        if feedback_type not in coverage_at_end:
            coverage_at_end[feedback_type] = []
        for f in files:
            df = pd.read_csv(f, names=columns)
            # plt.plot(df.num_execs, df.coverage, label=feedback_type)
            # plt.plot(df.num_execs, df.coverage, color=color, linewidth=0.2)
            # plt.scatter(df.num_execs, df.coverage, color=color)
            final_coverage_value = df.coverage.iloc[-1]
            coverage_at_end[feedback_type].append(final_coverage_value)

for ft, c in feedback_types:
    plot_files(ft, c)
# plt.xlabel("Num Execs")
# plt.ylabel("Coverage")
# plt.legend()
# plt.savefig("coverage_plot.png")
# plt.clf()

stats = {}
colors = []
labels = []
fig, axs = plt.subplots(len(feedback_types))
i = 0
x_buffer = 100
x_start = min([min(coverage_at_end[ft]) for ft in coverage_at_end]) - x_buffer
x_end = max([max(coverage_at_end[ft]) for ft in coverage_at_end]) + x_buffer
bins = np.linspace(x_start, x_end, 100)
for feedback_type, c in feedback_types:
    vals = coverage_at_end[feedback_type]
    if len(vals) > 0:
        m = mean(vals)
        s = stdev(vals)
        stats[feedback_type] = {
            "mean": m,
            "stdev": s,
            "num_vals": len(vals),
        }
    h, edges = np.histogram(vals, bins=bins)

    axs[i].stairs(h, bins, color=c, label=feedback_type)
    axs[i].set_xlim(x_start, x_end)
    axs[i].get_xaxis().set_visible(False)
    axs[i].set_ylim(0, 40)
    axs[i].legend()
    i += 1
axs[i - 1].get_xaxis().set_visible(True)
plt.savefig("coverage_hist.png")
plt.clf()

plt.bar([feedback_type for feedback_type, c in feedback_types], [stats[feedback_type]["mean"] for feedback_type, c in feedback_types], yerr=[stats[feedback_type]["stdev"] for feedback_type, c in feedback_types], color=[c for feedback_type, c in feedback_types])
# plt.ylim(x_start, x_end)
plt.xticks(rotation=45)
# plt.autoscale()
plt.savefig("coverage_bar.png", bbox_inches="tight")

def t_statistic(mean_1, mean_2, stdev_1, stdev_2, size_1, size_2):
    return (mean_1 - mean_2) / math.sqrt(stdev_1 * stdev_1 / size_1 + stdev_2 * stdev_2 / size_2)

# print(stats)
for feedback_type in stats:
    print(feedback_type, stats[feedback_type])

for i1 in range(len(stats)):
    ft1 = feedback_types[i1][0]
    for i2 in range(i1 + 1, len(stats)):
        ft2 = feedback_types[i2][0]
        print(ft1, ft2, scipy.stats.ttest_ind(coverage_at_end[ft1], coverage_at_end[ft2], equal_var=False))
        t = t_statistic(stats[ft1]["mean"], stats[ft2]["mean"], stats[ft1]["stdev"], stats[ft2]["stdev"], stats[ft1]["num_vals"], stats[ft2]["num_vals"])
        print(t, abs(t) > 2.262)
