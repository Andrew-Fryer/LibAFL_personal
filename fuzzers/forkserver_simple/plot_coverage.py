from matplotlib import pyplot as plt
import pandas as pd
import glob


# afl_edges_files = glob.glob('coverage_"AflEdges"_*.csv')
# const_true_files = glob.glob('coverage_"ConstTrue"_*.csv')

columns = ["num_execs", "coverage", "map_size"]
def plot_files(feedback_type, color):
    path = './coverage_logs/coverage_"{}"_*.csv'.format(feedback_type)
    files = glob.glob(path)
    for f in files:
        df = pd.read_csv(f, names=columns)
        # plt.plot(df.num_execs, df.coverage, label=feedback_type)
        plt.plot(df.num_execs, df.coverage, color=color)

plot_files("AflEdges", "red")
plot_files("ConstTrue", "blue")
plot_files("GrammarInput", "orange")
plot_files("GrammarOutput", "yellow")
plot_files("GrammarFull", "purple")
plt.xlabel("Num Execs")
plt.ylabel("Coverage")
# plt.legend()
plt.savefig("coverage_plot.png")
