'''
This script together with the others of the series CD_csv_creator_*.py were used in order to
generate .csv files used for the networks plotted using Gephi.
In particular, this script generates a .csv file formatted like this:
Source,Target
x,y
x,z
...

Moreover, it generates a .csv file used to plot the race barchart for the instagram data.

'''

import os
import random
import zipfile
import json
from json import JSONDecodeError

import matplotlib.pyplot as plt
import BrandsInfo
from datetime import datetime
import csv
import pandas as pd
import numpy as np

cwd = os.getcwd()
IGDataFolder = os.path.join(cwd, "..\..\IGData\Brands")

# insert in the .csv file classified users only
classif_users_only = True

dir_path = "output_csvcreators"
if not os.path.exists(os.path.join(cwd,dir_path)):
    os.mkdir(dir_path)

# use this variable to decide what data group to analyze
NY = False

if classif_users_only:
    if NY:
        df = pd.read_csv("user_cluster_NY.csv", usecols=["Id"])
    else:
        df = pd.read_csv("user_cluster_MI.csv", usecols=["Id"])
    classif_users_set = set(df.Id)

# analyse only main brands speficied below
main_brands = True

if main_brands:
    if NY:
        brands_to_analyze = [
            "tomford",
            "brandonmaxwell",
            "christopherjohnrogers",
            "mrselfportrait",
            "r13",
            "sandyliang",
            "area",
            "nicolemillernyc",
            "jasonwu",
            "palmangels",
            "proenzaschouler",
            "therow",
            "carolinaherrera",
            "jonathansimkhai",
            "dionlee",
            "verawanggang",
            "coach",
            "prabalgurung",
            "eckhaus_latta",
            "michaelkors",
            "marcjacobs"
        ]
    else:
        brands_to_analyze = [
            "filaeurope",
            "itscividini",
            "fendi",
            "boss",
            "gucci",
            "albertaferretti",
            "moncler",
            "jilsander",
            "moschino",
            "marni",
            "marcodevincenzo",
            "versace",
            "ferragamo",
            "msgm",
            "philosophyofficial",
            "bottegaveneta",
            "gcdswear",
            "agnonaofficial",
            "maxmara",
            "philippplein"
        ]


if NY:
    NYData = os.path.join(IGDataFolder, "NY")
    starting_date = datetime.strptime("07_02_2020", "%d_%m_%Y")
    end_date = datetime.strptime("13_02_2020", "%d_%m_%Y")
    # exclude directories
    zipFilesNY = [os.path.join(NYData, file) for file in os.listdir(NYData) if
                  os.path.isfile(os.path.join(NYData, file))]
    zipFiles = zipFilesNY

else:
    MIData = os.path.join(IGDataFolder, "MI")
    starting_date = datetime.strptime("18_02_2020", "%d_%m_%Y")
    end_date = datetime.strptime("25_02_2020", "%d_%m_%Y")
    # exclude directories
    zipFilesMI = [os.path.join(MIData, file) for file in os.listdir(MIData) if
                  os.path.isfile(os.path.join(MIData, file))]
    zipFiles = zipFilesMI


filename_clu = "_clustered_users.csv"
if NY:
    filename_clu = "NY" + filename_clu
else:
    filename_clu = "MI" + filename_clu


effectiveness_map = {}
base_users_map = {}
dates = []
for zipFile in zipFiles:
    archive = zipfile.ZipFile(zipFile, 'r')
    folder_date = zipFile.split("\\")[-1].replace(".zip", "")
    current_date = datetime.strptime(folder_date, "%d_%m_%Y")
    if starting_date <= current_date <= end_date:
        for brand in archive.filelist:
            brand_json = brand.filename.split("/")[-1]
            brand_id = brand_json.split(".")[0].replace(" ", "")
            byteFile = archive.read(folder_date + "/" + brand_json)
            try:
                jsonFile = json.loads(byteFile.decode("utf-8"))[0][brand_id]
            except JSONDecodeError:
                print("Cannot load the brand: " + brand_id)
                continue
            brand_username = jsonFile["username"]
            if brand_username in (brands_to_analyze if main_brands else (BrandsInfo.NYbrands if NY else BrandsInfo.MIbrands)):
                new_media_set = set([media["media_id"] for media in jsonFile["media_list"]])
                new_username_value = {"date": current_date, "media_set": new_media_set}
                if brand_username in effectiveness_map:
                    old_username_value = effectiveness_map[brand_username].pop()
                    old_media_set = old_username_value["media_set"]
                    old_date = old_username_value["date"]
                    dates.append(old_date)
                    new_posts = list(new_media_set.difference(old_media_set))
                    reached_accounts = []
                    for media in jsonFile["media_list"]:
                        if media["media_id"] in new_posts:
                            reached_accounts.extend(media["likers"])
                    reached_accounts = set(reached_accounts)
                    effectiveness_map[brand_username].append({"date": old_date, "reached_accounts": list(reached_accounts)})
                    effectiveness_map[brand_username].append(new_username_value)
                else:
                    effectiveness_map[brand_username] = [new_username_value]


x = range(len(effectiveness_map))
new_x = [4*i for i in x]
dates = set(dates)
dates = sorted(list(dates))
cumulative_eff_map_csv = {}
cumulative_map_race_bar = {}
auxiliary_list_race_bar = []
for date in dates:
    users = []
    tmp_eff_map_csv = []
    for key,value in effectiveness_map.items():
        for dict in value:
            if dict["date"] == date:
                tmp_eff_map_csv.append({"brand": key, "users": dict["reached_accounts"]})
                old_set = set()
                if key in cumulative_eff_map_csv.keys():
                    old_set = cumulative_eff_map_csv[key]

                old_set.update(set(dict["reached_accounts"]))
                cumulative_eff_map_csv[key] = old_set

                c_date = date.strftime("%b %d")
                ## This part of the code is dedicated to the creation of the race barchart
                if key in cumulative_map_race_bar.keys():
                    ex_dict = cumulative_map_race_bar[key]
                    ex_dict[c_date] = len(old_set)
                    cumulative_map_race_bar[key] = ex_dict
                else:
                    ex_dict = {c_date: len(old_set)}
                    cumulative_map_race_bar[key] = ex_dict
                auxiliary_list_race_bar.append(c_date)


    if NY:
        cumulative_csv_filename = "NY_brands_userwise_cumulative_"
    else:
        cumulative_csv_filename = "MI_brands_userwise_cumulative_"

    if classif_users_only:
        cumulative_csv_filename = cumulative_csv_filename + "cl_"

    cumulative_csv_filename = cumulative_csv_filename + datetime.strftime(date, "%d_%m_%Y") + ".csv"

    with open(os.path.join(dir_path,cumulative_csv_filename), 'w') as csvfile:
        fieldnames = ['Source', 'Target']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        with open(os.path.join(dir_path, filename_clu), 'w') as clus_users:
            for dicti in cumulative_eff_map_csv.items():
                if classif_users_only:
                    tmp_set = dicti[1].intersection(set([str(x) for x in classif_users_set]))
                else:
                    tmp_set = dicti[1]
                for user in tmp_set:
                    n_dict = {"Source": dicti[0], "Target": user}
                    writer.writerow(n_dict)


if NY:
    race_barchart_csv = "NY_race_barchart.csv"
else:
    race_barchart_csv = "MI_race_barchart.csv"

with open(os.path.join(dir_path, race_barchart_csv), 'w') as csvfile:
    fieldnames = ['brand']
    fieldnames.extend(np.unique(auxiliary_list_race_bar))
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    for key,value in cumulative_map_race_bar.items():
        value["brand"] = key
        writer.writerow(value)
