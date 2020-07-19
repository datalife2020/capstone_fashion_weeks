'''
---------------------------------------------------------------------------------------------------
THIS SCRIPT IS AN INTERMEDIATE ONE, IT IS NOT PART OF THE FINAL OUTPUT. IT HAS BEEN USED IN ORDER
TO GATHER INSIGHTS ABOUT THE COLLECTED DATA DURING THE EXPLORATORY DATA ANALYSIS
---------------------------------------------------------------------------------------------------

This scripts uses the results obtained from LDA in order to perform clustering on the probabilities.
'''


import pandas as pd
import os
import ast
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans
from statsmodels.graphics.mosaicplot import mosaic
from itertools import product


def from_string_to_nparray(row):
    row['topic_probability'] = np.array(ast.literal_eval(row['topic_probability']))
    return row

def majority_voting(row):
    # find the maximum probability and assign that topic to the considered user
    cluster = np.where(row['topic_probability'] == np.amax(row['topic_probability']))
    if np.array(cluster).shape[1] > 1:
        row['topic_assigned'] = float("nan")
    else:
        row['topic_assigned'] = np.array(cluster).max()
    return row


max_prob_classifier = True
do_mosaic = True
plot_points = False
NY = True
do_pca = False
do_DBSCAN = False
do_kmeans = False

cwd = os.getcwd()

if NY:
    input_csv_filename = "users_topic_3_probability_NY.csv"
    csv_users_filter = set(pd.read_csv(os.path.join(cwd, "user_cluster_NY.csv")).Id)
else:
    input_csv_filename = "users_topic_3_probability_MI.csv"
    csv_users_filter = set(pd.read_csv(os.path.join(cwd, "user_cluster_MI.csv")).Id)


input_folder_from_lda = os.path.join(cwd, "input_text_clustering_from_lda")
output_folder_path = os.path.join(cwd, "output_text_clustering")
input_from_csv_creators_folder = os.path.join(cwd, "output_csvcreators")

df_csv_users = pd.read_csv(os.path.join(input_folder_from_lda, input_csv_filename))

# intersect all the collected users with the ones filtered
df_csv_users_filter = pd.DataFrame(csv_users_filter, columns=["user"])
print("Dataframe users shape before filtering: " + str(df_csv_users.shape))
print("Dataframe filter dimensions : " + str(df_csv_users_filter.shape))
df_csv_users_filtered = pd.merge(df_csv_users, df_csv_users_filter, on=["user"])
print("Dataframe users shape after filtering: " + str(df_csv_users_filtered.shape))

df_csv_users_filtered = df_csv_users_filtered.apply(from_string_to_nparray, axis=1)

if max_prob_classifier:
    df_csv_users_filtered["topic_assigned"] = ""
    df_csv_users_filtered = df_csv_users_filtered.apply(majority_voting, axis=1)
    df_csv_users_filtered.dropna(inplace=True)
    user_clusters = df_csv_users_filtered.filter(['user','topic_assigned'], axis=1)
    user_clusters.rename(columns={'user': 'Id'}, inplace=True)
    if NY:
        user_clusters.to_csv(os.path.join(output_folder_path, "NY_users_topic_assigned_max_prob.csv"), index=False)
    else:
        user_clusters.to_csv(os.path.join(output_folder_path, "MI_users_topic_assigned_max_prob.csv"), index=False)

topic_probabilities = np.vstack(np.array(df_csv_users_filtered['topic_probability']))

if do_DBSCAN:
    eps = 0.02
    min_samples = 20
    DBSCAN_labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(topic_probabilities)
    clustering_results = pd.DataFrame(columns=["Id", "user_cluster"])
    clustering_results["Id"] = df_csv_users_filtered["user"]
    clustering_results["user_cluster"] = DBSCAN_labels
    if NY:
        clustering_results.to_csv(os.path.join(output_folder_path, "NY_cl_DBSCAN_e{}_m{}.csv").format(eps, min_samples), index=False)
    else:
        clustering_results.to_csv(os.path.join(output_folder_path, "MI_cl_DBSCAN_e{}_m{}.csv").format(eps, min_samples), index=False)

if do_kmeans:
    n_clusters = len(topic_probabilities[0])
    KMeans_labels = KMeans(n_clusters=n_clusters, init="k-means++").fit_predict(topic_probabilities)
    clustering_results = pd.DataFrame(columns=["Id", "user_cluster"])
    clustering_results["Id"] = df_csv_users_filtered["user"]
    clustering_results["user_cluster"] = KMeans_labels
    if NY:
        clustering_results.to_csv(os.path.join(output_folder_path, "NY_cl_KMeans_c{}.csv").format(n_clusters), index=False)
    else:
        clustering_results.to_csv(os.path.join(output_folder_path, "MI_cl_KMeans_c{}.csv").format(n_clusters), index=False)


if do_mosaic:
    # up to now does not work with class assigned via clutering algorithm
    if NY:
        clustered_users = pd.read_csv(os.path.join(input_from_csv_creators_folder, "NY_clustered_users.csv"))
    else:
        clustered_users = pd.read_csv(os.path.join(input_from_csv_creators_folder, "MI_clustered_users.csv"))

    if max_prob_classifier:
        tuples = list(product(clustered_users.brand.to_list(), ["t{}".format(i) for i in range(len(topic_probabilities[0]))]))
    else:
        clusters = np.unique(clustering_results["user_cluster"].to_list())
        tuples = list(product(clustered_users.brand.to_list(), clusters))
    index_mosaic = pd.MultiIndex.from_tuples(tuples, names=['first', 'second'])

    data = []
    for index, row in clustered_users.iterrows():
        tmp_df = pd.DataFrame(columns=["Id"])
        tmp_df["Id"] = ast.literal_eval(row["users"])
        tmp_df["Id"] = tmp_df["Id"].astype("int64")
        # find all the clustered users for this brand
        if max_prob_classifier:
            tmp_df = pd.merge(tmp_df, user_clusters, on="Id")
        else:
            tmp_df = pd.merge(tmp_df, clustering_results, on="Id")
        topics_number = tmp_df.groupby
        if max_prob_classifier:
            data.extend(tmp_df.groupby("topic_assigned").count()["Id"].to_list())
        else:
            data.extend(tmp_df.groupby("user_cluster").count()["Id"].to_list())

    data = pd.Series(data, index = index_mosaic)
    labels = lambda _: ""
    if NY:
        if max_prob_classifier:
            plot_filename = "NY_mosaic_chart_{}_topics.pdf".format(len(topic_probabilities[0]))
            plot_title = "Mosaic chart NY maximum probability"
        else:
            plot_filename = "NY_K_mosaic_chart_{}_topics.pdf".format(len(topic_probabilities[0]))
            plot_title = "Mosaic chart NY K-Means"
    else:
        if max_prob_classifier:
            plot_filename = "MI_mosaic_chart_{}_topics.pdf".format(len(topic_probabilities[0]))
            plot_title = "Mosaic chart MI maximum probability"
        else:
            plot_filename = "MI_K_mosaic_chart_{}_topics.pdf".format(len(topic_probabilities[0]))
            plot_title = "Mosaic chart MI K-Means"
    fig, rects = mosaic(data, title=plot_title, gap=0.01, label_rotation=[90,0], labelizer=labels)
    fig.set_size_inches(15, 10)
    fig.savefig(os.path.join(output_folder_path, plot_filename), bbox_inches='tight', format="pdf")
    plt.show()

if do_pca:
    pca = PCA(n_components=2)
    x = StandardScaler().fit_transform(topic_probabilities)
    principalComponents = pca.fit_transform(x)
    principalDf = pd.DataFrame(data=principalComponents, columns=['pc1', 'pc2'])



if plot_points:
    # if do_pca is true then the dimensions are two and not three
    if do_pca:
        plt.figure(figsize=(15,13))
        if do_DBSCAN:
            scatter = plt.scatter(principalDf.pc1, principalDf.pc2, c=DBSCAN_labels, cmap="Pastel1")
            plt.legend(*scatter.legend_elements(),
                                loc="upper right", title="Classes")
        elif do_kmeans:
            scatter = plt.scatter(principalDf.pc1, principalDf.pc2, c=KMeans_labels, cmap="Pastel1")
            plt.legend(*scatter.legend_elements(),
                                loc="upper right", title="Classes")
        else:
            plt.scatter(principalDf.pc1, principalDf.pc2)
        plt.xlabel("pc1")
        plt.ylabel("pc2")
        if do_DBSCAN or do_kmeans:
            plt.title("PCA of the topic probability vector considered as embedding space with the related clusters")
        else:
            plt.title("PCA of the topic probability vector considered as embedding space")
        if NY:
            if do_DBSCAN:
                plot_filename = "NY_scatterplot_pca_{}_topics_DBSCAN_e{}_m{}.pdf".format(len(topic_probabilities[0]), eps, min_samples)
            elif do_kmeans:
                plot_filename = "NY_scatterplot_pca_{}_topics_KMeans.pdf".format(len(topic_probabilities[0]))
            else:
                plot_filename = "NY_scatterplot_pca_{}_topics.pdf".format(len(topic_probabilities[0]))
        else:
            if do_DBSCAN:
                plot_filename = "MI_scatterplot_pca_{}_topics_DBSCAN_e{}_m{}.pdf".format(len(topic_probabilities[0]), eps, min_samples)
            elif do_kmeans:
                plot_filename = "NY_scatterplot_pca_{}_topics_KMeans.pdf".format(len(topic_probabilities[0]))
            else:
                plot_filename = "MI_scatterplot_pca_{}_topics.pdf".format(len(topic_probabilities[0]))
        plt.savefig(os.path.join(output_folder_path, plot_filename), bbox_inches='tight', format="pdf")
        plt.show()
    else:
        ## show data without any clustering
        fig = plt.figure(figsize=(15, 13))
        ax = Axes3D(fig)
        ax.scatter(topic_probabilities[:,0],topic_probabilities[:,1], topic_probabilities[:,2], cmap=plt.get_cmap('Pastel1'))
        ax.set_xlabel("topic 1")
        ax.set_ylabel("topic 2")
        ax.set_zlabel("topic 3")
        ax.set_title("Data points")
        if NY:
            plot_filename = "NY_scatterplot_lda_3d_{}_topics.pdf".format(len(topic_probabilities[0]))
        else:
            plot_filename = "MI_scatterplot_lda_3d_{}_topics.pdf".format(len(topic_probabilities[0]))
        fig.savefig(os.path.join(output_folder_path, plot_filename), bbox_inches='tight', format="pdf")
        fig.show()
