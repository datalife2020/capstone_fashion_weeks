'''
---------------------------------------------------------------------------------------------------
THIS SCRIPT IS AN INTERMEDIATE ONE, IT IS NOT PART OF THE FINAL OUTPUT. IT HAS BEEN USED IN ORDER
TO GATHER INSIGHTS ABOUT THE COLLECTED DATA DURING THE EXPLORATORY DATA ANALYSIS
---------------------------------------------------------------------------------------------------

This script has been used in order to deal with the quantitative data of each user: follower_count,
following_count and media_count. For these dimensions, some clustering approaches have been tried.
'''


import os
import zipfile
import json
from json import JSONDecodeError
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn import cluster
import csv
import pandas as pd
from sklearn.neighbors import KernelDensity
import matplotlib.colors as mcolors

def kde2D(x, y, bandwidth, xbins=100j, ybins=100j, **kwargs):
    """Build 2D kernel density estimate (KDE)."""

    # create grid of sample locations (default: 100x100)
    xx, yy = np.mgrid[x.min():x.max():xbins,
                      y.min():y.max():ybins]

    xy_sample = np.vstack([yy.ravel(), xx.ravel()]).T
    xy_train  = np.vstack([y, x]).T

    kde_skl = KernelDensity(bandwidth=bandwidth, **kwargs)
    kde_skl.fit(xy_train)

    # score_samples() returns the log-likelihood of the samples
    z = np.exp(kde_skl.score_samples(xy_sample))
    return xx, yy, np.reshape(z, xx.shape)

cwd = os.getcwd()
IGDataFolder = os.path.join(cwd, r"..\..\IGData\User_info")
output_folder_name = "output_clustering"
output_folder_path = os.path.join(cwd, output_folder_name)

if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)


# use this variable to decide what data group to analyze
NY = False

# use this variable to plot the data points
plot_points = True

# use this variable to plot the KMEANS result
plot_KMEANS = True
plot_elbow = False

# use this variable to plot the DBSCAN result
plot_DBSCAN = True

# use this variable to create the csv file user,cluster
user_cluster_csv = True

kde = True

if NY:
    NYData = os.path.join(IGDataFolder, "NY")
    # exclude directories
    zipFilesNY = [os.path.join(NYData, file) for file in os.listdir(NYData) if
                  os.path.isfile(os.path.join(NYData, file))]
    zipFiles = zipFilesNY

else:
    MIData = os.path.join(IGDataFolder, "MI")
    # exclude directories
    zipFilesMI = [os.path.join(MIData, file) for file in os.listdir(MIData) if
                  os.path.isfile(os.path.join(MIData, file))]
    zipFiles = zipFilesMI

archive = zipfile.ZipFile(zipFiles[0], 'r')
input_to_clustering = []
users = []
user_full = []
users_for_topic_analysis = []
users_csv = []
for file in archive.filelist:
    if "bio" in file.filename:
        byteFile = archive.read(file)
        try:
            jsonFile = json.loads(byteFile.decode("utf-8"))
        except JSONDecodeError:
            print("Cannot load the file" + str(file))
            continue
        for json_ in jsonFile:
            user_full.append(json_["pk"])

            if json_["media_count"] <= 10000 and \
                    json_["follower_count"] <= 100000 and \
                    json_["following_count"] <= 50000:
                if json_["pk"] in users:
                    continue
                users.append(json_["pk"])
                input_to_clustering.append([json_["follower_count"],
                                            json_["following_count"],
                                            json_["media_count"]])
                users_for_topic_analysis.append([json_["pk"], json_["biography"]])

input_to_clustering = np.array(input_to_clustering)
input_to_clustering = MinMaxScaler().fit_transform(input_to_clustering)
print(input_to_clustering.shape)

if kde:
    bandwidth = 0.2
    xx, yy, zz = kde2D(input_to_clustering[:,1], input_to_clustering[:,2], bandwidth)

    plt.pcolormesh(xx, yy, zz)
    plt.title("KDE with bandwidth="+str(bandwidth))
    plt.xlabel("follower_count")
    plt.ylabel("following_count")
    plt.savefig(os.path.join(output_folder_path, "kde_bandwidth_" + str(bandwidth) + ".pdf"), bbox_inches='tight', format="pdf")
    plt.show()

if plot_points:
    ## show data without any clustering
    fig = plt.figure(figsize=(15, 13))
    ax = Axes3D(fig)
    ax.scatter(input_to_clustering[:,0],input_to_clustering[:,1], input_to_clustering[:,2], cmap=plt.get_cmap('Pastel1'))
    ax.set_xlabel("follower_count")
    ax.set_ylabel("following_count")
    ax.set_zlabel("media_count")
    ax.set_title("Data points")
    fig.savefig(os.path.join(output_folder_path, "scatterplot_3d.pdf"), bbox_inches='tight', format="pdf")
    fig.show()


if plot_DBSCAN:
    ## DBSCAN
    model_DBSCAN = cluster.DBSCAN(eps=0.05, min_samples=15).fit(input_to_clustering)
    fig = plt.figure(figsize=(15, 13))
    ax = Axes3D(fig)
    ax.scatter(input_to_clustering[:,0],input_to_clustering[:,1], input_to_clustering[:,2], cmap=plt.get_cmap('Pastel1'), c=model_DBSCAN.labels_)
    ax.set_xlabel("follower_count")
    ax.set_ylabel("following_count")
    ax.set_zlabel("media_count")
    ax.set_title("Data points clustered with DBSCAN")
    fig.savefig(os.path.join(output_folder_path, "scatterplot_3d_DBSCAN.pdf"), bbox_inches='tight', format="pdf")
    fig.show()

if plot_KMEANS:
    ## K-MEANS

    if plot_elbow:
        K = range(1, 30)
        inertias = []
        for k in K:
            model = cluster.KMeans(n_clusters=k, init='k-means++').fit(input_to_clustering)
            inertias.append(model.inertia_)

        plt.figure()
        plt.plot(K, inertias, "bx-")
        plt.title("WSS values for k-values in k-means clustering")
        plt.xlabel("k values")
        plt.ylabel("Inertia (WSS)")
        plt.ticklabel_format(style='plain')
        plt.savefig(os.path.join(output_folder_path, "inertias.pdf"), bbox_inches='tight', format="pdf")
        plt.show()
    else:
        selected_k = 5
        model_selected = cluster.KMeans(n_clusters=selected_k, init='k-means++').fit(input_to_clustering)

    if user_cluster_csv:
        with open("user_cluster.csv", 'w') as csvfile:
            fieldnames = ['Id', 'user_cluster']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
            writer.writeheader()
            for i in range(len(users)):
                n_dict = {"Id": users[i], "user_cluster": model_selected.labels_[i]}
                writer.writerow(n_dict)


    fig = plt.figure(figsize=(15, 13))
    ax = fig.add_subplot(111, projection='3d')
    df = pd.DataFrame(dict(x=input_to_clustering[:,0],
                           y=input_to_clustering[:,1],
                           z=input_to_clustering[:,2],
                           label=model_selected.labels_))

    groups = df.groupby("label")

    for color,group in groups:
        ax.plot(group["x"], group["y"], group["z"], marker="o", linestyle="", label=color, alpha=0.3)

    ax.set_xlabel("follower_count")
    ax.set_ylabel("following_count")
    ax.set_zlabel("media_count")
    ax.set_title("Data points clustered with K-MEANS with k="+str(selected_k))
    ax.legend()
    fig.savefig(os.path.join(output_folder_path, "scatterplot_3d_KMEANS.pdf"), bbox_inches='tight', format="pdf")
    fig.show()
    print(len(model_selected.labels_))
