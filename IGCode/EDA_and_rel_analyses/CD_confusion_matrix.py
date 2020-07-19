'''
---------------------------------------------------------------------------------------------------
THIS SCRIPT IS AN INTERMEDIATE ONE, IT IS NOT PART OF THE FINAL OUTPUT. IT HAS BEEN USED IN ORDER
TO GATHER INSIGHTS ABOUT THE COLLECTED DATA DURING THE EXPLORATORY DATA ANALYSIS
---------------------------------------------------------------------------------------------------

This script has been used in order to plot two clustermaps, one for NYFW and the other for MIFW.
These visualizations were used in order to understand quantitatively how many users are shared among
brands.
'''


import pandas as pd
import os
import re
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import numpy as np

NY = True

cwd = os.getcwd()

dir_path = os.path.join(cwd, "output_confusion_matrix")
if not os.path.exists(dir_path):
    os.mkdir(dir_path)

clustermap_filename = "_clustermap.pdf"
if NY:
    brands_users_csv_filename = os.path.join(cwd, "output_csvcreators", "NY_clustered_users.csv")
    clustermap_filename = os.path.join(dir_path, "NY" + clustermap_filename)
else:
    brands_users_csv_filename = os.path.join(cwd, "output_csvcreators", "MI_clustered_users.csv")
    clustermap_filename = os.path.join(dir_path, "MI" + clustermap_filename)

df = pd.read_csv(brands_users_csv_filename)

for i in range(len(df.users)):
    df.users[i] = re.sub("\\'|\[|\]", "", df.users[i]).split(",")

brands = []
shared_users = []
for tuple1 in df.itertuples():
    brands.append(tuple1.brand)
    shared_users_list = []
    for tuple2 in df.itertuples():
        shared_users_set = set(tuple1.users).intersection(tuple2.users)
        shared_users_list.append(len(shared_users_set))
    shared_users.append(shared_users_list)

g = sns.clustermap(shared_users, row_cluster=False, col_cluster=False)
g.ax_heatmap.set_yticklabels(brands, rotation=0)
g.ax_heatmap.set_xticklabels(brands, rotation=90)
g.fig.suptitle('Shared accounts among brands')
plt.show()
g.savefig(clustermap_filename, bbox_inches='tight', format="pdf")
