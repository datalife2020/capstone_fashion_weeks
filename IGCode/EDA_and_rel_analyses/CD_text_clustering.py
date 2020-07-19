'''
This script has been used to generate the final results obtained through Word2Vec, it performs word embedding, then it averages
the embedding vectors of the words of every biography and uses this result in order to perform clustering. At the end it just
plot the mosaic chart with the result of the clustering process.
'''

import os
import json
import re
from json import JSONDecodeError
import zipfile
from operator import add
import nltk as nltk
import pandas as pd
from gensim.models import Word2Vec, word2vec, doc2vec
import csv
import numpy as np
from wordcloud import WordCloud
from collections import Counter

from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
from itertools import product
import ast

from statsmodels.graphics.mosaicplot import mosaic

def build_corpus(data):
    corpus = []

    for sentence in data[0].iteritems():
        word_list = sentence[1].split(" ")
        corpus.append(word_list)

    return corpus

def clean_sentence(val):
    # remove chars that are not letters or numbers, downcase, then remove stop words
    regex = re.compile('([^\s\w]|_)+')
    sentence = regex.sub(' ', val).lower()
    sentence = sentence.replace("\n", " ")
    sentence = sentence.split()

    for word in list(sentence):
        if word in STOP_WORDS or len(word) <= 1:
            sentence.remove(word)

    sentence = " ".join(sentence)
    return sentence


def clean_dataframe(data):
    # drop nans, then apply 'clean_sentence' function to question1 and 2
    data = data.dropna(how="any")
    data[0] = data[0].apply(clean_sentence)

    return data

def avg_embedding_for_docs(model_w2v, sentences, users):
    doc_embeddings = {}
    id = 0
    for i in range(len(sentences)):
        word_list = sentences[i]
        id = users[i]
        avg_embedding = 0
        tmp_word_list = []
        for word in word_list:
            if word in model_w2v.wv.vocab:
                avg_embedding = avg_embedding + model_w2v.wv[word]
                tmp_word_list.append(word)
        if len(tmp_word_list) != 0:
            avg_embedding = avg_embedding/len(tmp_word_list)
            doc_embeddings[id] = {"avg_embedding": avg_embedding, "word_list": tmp_word_list}
    return doc_embeddings

def tsne_plot(model=None, tokens=None, labels=None):
    "Creates and TSNE model and plots it"

    if tokens is None:
        labels = []
        tokens = []
        for word in model.wv.vocab:
            tokens.append(model[word])
            labels.append(word)

    tsne_model = TSNE(perplexity=40, n_components=2, init='pca', random_state=23)
    new_values = tsne_model.fit_transform(tokens)

    x = []
    y = []
    for value in new_values:
        x.append(value[0])
        y.append(value[1])

    plt.figure(figsize=(16, 16))
    #for i in range(len(x)):
    scatter = plt.scatter(x, y, c=labels)
    plt.legend(*scatter.legend_elements(),loc="upper right", title="Clusters")
        # if labels is not None:
        #     plt.scatter(x[i], y[i])
        #     plt.annotate(labels[i],
        #                  xy=(x[i], y[i]),
        #                  xytext=(5, 2),
        #                  textcoords='offset points',
        #                  ha='right',
        #                  va='bottom')
    if model is not None:
        if NY:
            plt.title("t-SNE biography's words NY")
            tsne_filename = "tSNE_w2v_NY.pdf"
        else:
            plt.title("t-SNE biography's words MI")
            tsne_filename = "tSNE_w2v_MI.pdf"
        plt.savefig(os.path.join(output_folder_path, tsne_filename), bbox_inches='tight', format="pdf")
    else:
        if NY:
            plt.title("t-SNE biography NY")
            tsne_filename = "tSNE_biography_avg_NY.pdf"
        else:
            plt.title("t-SNE biography MI")
            tsne_filename = "tSNE_biography_avg_MI.pdf"
        plt.savefig(os.path.join(output_folder_path, tsne_filename), bbox_inches='tight', format="pdf")
    plt.show()

def remove_empty_lists(corpus, users):

    length = len(corpus)
    i = 0
    while i < length:
        if len(corpus[i]) == 1 and not corpus[i].pop():
            del corpus[i]
            del users[i]
            length = length - 1
        else:
            i = i + 1

    return corpus, users

cwd = os.getcwd()
IGDataFolder = os.path.join(cwd, r"..\..\IGData\User_info")
output_folder_name = "output_text_clustering"
output_folder_path = os.path.join(cwd, output_folder_name)
input_from_csv_creators_folder = os.path.join(cwd, "output_csvcreators")

if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

# use this variable to decide what data group to analyze
NY = True
do_mosaic = True
do_clustering = True
do_word_cloud = True

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
sentences = []
users = []
for file in archive.filelist:
    if "bio" in file.filename:
        byteFile = archive.read(file)
        try:
            jsonFile = json.loads(byteFile.decode("utf-8"))
        except JSONDecodeError:
            print("Cannot load the file" + str(file))
            continue
        for json_ in jsonFile:
            if json_["media_count"] <= 10000 and \
                    json_["follower_count"] <= 100000 and \
                    json_["following_count"] <= 50000:
                if json_["pk"] in users:
                    continue
                users.append(json_["pk"])
                sentences.append(json_["biography"])

STOP_WORDS = nltk.corpus.stopwords.words()

data = pd.DataFrame(sentences)

data = clean_dataframe(data)
print(data.head(5))

corpus = build_corpus(data)
print(corpus[0:2])

corpus, users = remove_empty_lists(corpus, users)

model_w2v = word2vec.Word2Vec(corpus, size=100, window=20, min_count=30, workers=4)

avg_doc_embedding = avg_embedding_for_docs(model_w2v, corpus, users)
input_to_clustering=[]
ids = []
words_list = []
for key,value in avg_doc_embedding.items():
    ids.append(key)
    input_to_clustering.append(value["avg_embedding"])
    words_list.append(value["word_list"])

if do_clustering:
    clusters_no = 3
    print("starting clustering")
    model_GM = GaussianMixture(n_components=clusters_no, covariance_type='full').fit(input_to_clustering)
    print("clustering finished")
    labels = model_GM.predict(input_to_clustering)
    if NY:
        csv_filename = "NY_users_clusters_c{}.csv"
    else:
        csv_filename = "MI_users_clusters_c{}.csv"

    with open(os.path.join(output_folder_path, csv_filename.format(clusters_no)), 'w') as csvfile:
        fieldnames = ['Id', 'user_cluster']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        for i in range(len(ids)):
            n_dict = {"Id": ids[i], "user_cluster": labels[i]}
            writer.writerow(n_dict)


if do_word_cloud:
    labels_unique = np.unique(labels)
    words_list = np.array(words_list)
    for i in labels_unique:
        i_pos = np.where(labels == i)
        tmp_word_list = words_list[i_pos]
        flatten_word_list = [item for sublist in tmp_word_list for item in sublist]
        wordcloud = WordCloud(max_words=100, max_font_size=150, width=1600, height=800, background_color="white").generate(" ".join(flatten_word_list))

        if NY:
            csv_words_count_filename = os.path.join(output_folder_path, "NY_words_count_cluster_{}.csv")
        else:
            csv_words_count_filename = os.path.join(output_folder_path, "MI_words_count_cluster_{}.csv")

        counter = Counter(flatten_word_list)
        most_occur = counter.most_common(100)
        words_count = pd.DataFrame(most_occur, columns=["word", "count"])
        words_count.to_csv(csv_words_count_filename.format(str(i)))


        # Display the generated image:
        plt.figure( figsize=(20,10), facecolor='k')
        plt.imshow(wordcloud)
        plt.axis("off")
        if NY:
            plot_title = "NY Word cloud from cluster {}".format(str(i))
            plot_filename = "NY_word_cloud_cluster_{}.png".format(str(i))
        else:
            plot_title = "MI Word cloud from cluster {}".format(str(i))
            plot_filename = "MI_word_cloud_cluster_{}.png".format(str(i))

        plt.title(plot_title)
        plt.savefig(os.path.join(output_folder_path, plot_filename), bbox_inches='tight', format="png")
        plt.show()


if do_mosaic:
    if NY:
        clustered_users = pd.read_csv(os.path.join(input_from_csv_creators_folder, "NY_clustered_users.csv"))
    else:
        clustered_users = pd.read_csv(os.path.join(input_from_csv_creators_folder, "MI_clustered_users.csv"))


    clusters = np.unique(labels)
    tuples = list(product(clustered_users.brand.to_list(), clusters))
    index_mosaic = pd.MultiIndex.from_tuples(tuples, names=['first', 'second'])

    clustering_results = pd.DataFrame(columns=["Id", "user_cluster"])
    clustering_results["Id"] = ids
    clustering_results["user_cluster"] = labels

    data = []
    for index, row in clustered_users.iterrows():
        tmp_df = pd.DataFrame(columns=["Id"])
        tmp_df["Id"] = ast.literal_eval(row["users"])
        tmp_df["Id"] = tmp_df["Id"].astype("int64")
        # find all the clustered users for this brand
        tmp_df = pd.merge(tmp_df, clustering_results, on="Id")
        topics_number = tmp_df.groupby
        data.extend(tmp_df.groupby("user_cluster").count()["Id"].to_list())

    data = pd.Series(data, index=index_mosaic)
    labelizers = lambda _: ""
    if NY:
        plot_filename = "NY_GMM_mosaic_chart_{}_clusters.pdf".format(clusters_no)
        plot_title = "Mosaic chart NY GMM"
    else:
        plot_filename = "MI_K_mosaic_chart_{}_clusters.pdf".format(clusters_no)
        plot_title = "Mosaic chart MI GMM"
    fig, rects = mosaic(data, title=plot_title, gap=0.01, label_rotation=[90,0], labelizer=labelizers)
    fig.set_size_inches(15, 10)
    fig.savefig(os.path.join(output_folder_path, plot_filename), bbox_inches='tight', format="pdf")
    plt.show()


tsne_plot(tokens=input_to_clustering[:5000], labels=labels[:5000])

print(np.unique(labels, return_counts=True))
