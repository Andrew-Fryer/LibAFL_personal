from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import glob
from statistics import mean, stdev
import math
import scipy


class Distribution:
    def __init__(self, name="", data_points=[], color='red'):
        self.name = name
        self.data_points = data_points
        self.mean = mean(data_points)
        self.stdev = stdev(data_points)
        self.num_vals = len(data_points)
        self.min = min(data_points)
        self.max = max(data_points)
        self.color = color

class DistributionsForComparison:
    def __init__(self, name, feedback_types, extractor):
        self.name = name
        self.distributions = []
        for dir_path, color in feedback_types:
            d = extractor(dir_path, color)
            self.distributions.append(d)

    def plot_hist(self):
        fig, axs = plt.subplots(len(self.distributions))
        x_start = min([d.min for d in self.distributions])
        x_end = max([d.max for d in self.distributions])
        diff = x_end - x_start
        x_buffer = diff / 5
        x_start -= x_buffer
        x_end += x_buffer
        bins = np.linspace(x_start, x_end, 100)
        i = 0
        for d in self.distributions:
            h, edges = np.histogram(d.data_points, bins=bins)
            axs[i].stairs(h, bins, color=d.color, label=d.name)
            axs[i].set_xlim(x_start, x_end)
            axs[i].get_xaxis().set_visible(False)
            axs[i].set_ylim(0, 40)
            axs[i].legend()
            i += 1
        axs[i - 1].get_xaxis().set_visible(True)
        axs[0].set_title(self.name)
        plt.savefig(self.name + "_hist.png")
        plt.clf()

    def plot_bar(self):
        plt.bar(
            [d.name for d in self.distributions],
            [d.mean for d in self.distributions],
            yerr=[d.stdev for d in self.distributions],
            color=[d.color for d in self.distributions]
        )
        # plt.ylim(x_start, x_end)
        plt.xticks(rotation=45)
        # plt.autoscale()
        plt.title(self.name)
        plt.savefig(self.name + "_bar.png", bbox_inches="tight")
        plt.clf()

    def print_stats(self):
        for d in self.distributions:
            print(d.name + ":")
            print("\tmean:\t" + str(d.mean))
            print("\tstdev:\t" + str(d.stdev))
        def t_statistic(mean_1, mean_2, stdev_1, stdev_2, size_1, size_2):
            # if size_1 == 0 or size_2 == 0 or stdev_1 == 0 and stdev_2 == 0:
            #     return None
            if mean_1 == mean_2:
                return 0
            return (mean_1 - mean_2) / math.sqrt(stdev_1 * stdev_1 / size_1 + stdev_2 * stdev_2 / size_2)
        
        for i1 in range(len(self.distributions)):
            d1 = self.distributions[i1]
            for i2 in range(i1 + 1, len(self.distributions)):
                d2 = self.distributions[i2]
                t = t_statistic(d1.mean, d2.mean, d1.stdev, d2.stdev, d1.num_vals, d2.num_vals)
                print(d1.name, d2.name, scipy.stats.ttest_ind(d1.data_points, d2.data_points, equal_var=False), t, abs(t) > 2.262)

def extract_final_input_grammar_coverage(dir_path, color):
    data_points = []
    for path in glob.glob(dir_path + '/*/input_grammar_coverage'):
        with open(path, 'rb') as f:
            binary = f.read()
            count = 0
            for b in binary:
                if b != 0x00:
                    count += 1
            data_points.append(count)
    return Distribution(dir_path, data_points, color)

def extract_final_corpus_size(dir_path, color):
    data_points = []
    for path in glob.glob(dir_path + '/*/num_elements_in_corpus'):
        with open(path) as f:
            for line in f:
                pass
            last_line = line
            num_elements_in_corpus = line.split(' ')[-1]
            data_points.append(int(num_elements_in_corpus))
    return Distribution(dir_path, data_points, color)

def extract_final_coverage(dir_path, color):
    data_points = []
    for path in glob.glob(dir_path + '/*/coverage.csv'):
        with open(path) as f:
            for line in f:
                pass
            last_line = line
            num_execs, coverage, map_size = line.split(', ')
            data_points.append(int(coverage))
    return Distribution(dir_path, data_points, color)

feedback_types = [
    ("AflEdges", "red"),
    # ("GrammarFull", "purple"),
    ("GrammarInput_parses_83e25040", "grey"),
    ("GrammarInput_max_bucketing_6fefb40c", "orange"),
    ("GrammarInput_unique_00ec3f10", "yellow"),
    ("GrammarOutput_unique_00ec3f10", "yellow"),
    ("ConstTrue", "blue"),
    ("ConstTrue_83e25040", "purple"),
    ("Random_32a65bc0", "brown"),
]

for_comparsion = [
    ('Code Coverage', extract_final_coverage),
    ('Corpus Size', extract_final_corpus_size),
    ('Grammar Coverage', extract_final_input_grammar_coverage),
]
for name, extractor in for_comparsion:
    ds = DistributionsForComparison(name, feedback_types, extractor)
    ds.print_stats()
    ds.plot_hist()
    ds.plot_bar()
print('done')
