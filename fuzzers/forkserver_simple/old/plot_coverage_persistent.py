from matplotlib import pyplot as plt
import pandas as pd


# plt.rcParams["figure.figsize"] = [7.00, 3.50]
# plt.rcParams["figure.autolayout"] = True
columns = ["num_execs", "coverage", "map_size"]
# df_normal = pd.read_csv("coverage.normal.csv", names=columns)
# df_no_edges_objective = pd.read_csv("coverage.no_edges_objective.csv", names=columns)
# df_feedback_const_true = pd.read_csv("coverage.feedback_const_true_and_only_queue_scheduler.csv", names=columns)
# df_feedback_const_true_2 = pd.read_csv("coverage.feedback_const_true_and_only_queue_scheduler_2.csv", names=columns)
df_persistent_feedback_const_true = pd.read_csv("coverage.persistent.feedback_const_true_and_only_queue_scheduler.csv", names=columns)
df_persistent_normal = pd.read_csv("coverage.persistent.normal.csv", names=columns)
# print("Contents in csv file:", df_normal)
# plt.plot(df_normal.num_execs, df_normal.coverage, label="normal")
# plt.plot(df_no_edges_objective.num_execs, df_no_edges_objective.coverage, label="no edges objective")
# plt.plot(df_feedback_const_true.num_execs, df_feedback_const_true.coverage, label="no feedback")
# plt.plot(df_feedback_const_true_2.num_execs, df_feedback_const_true_2.coverage, label="no feedback 2")
plt.plot(df_persistent_feedback_const_true.num_execs, df_persistent_feedback_const_true.coverage, label="persistent no feedback")
plt.plot(df_persistent_normal.num_execs, df_persistent_normal.coverage, label="persistent normal")
plt.xlabel("Num Execs")
plt.ylabel("Coverage")
plt.legend()

x1, x2, y1, y2 = plt.axis()  
plt.axis((x1, x2, 1462, 1464))

plt.savefig("coverage_persistent_plot.png")
