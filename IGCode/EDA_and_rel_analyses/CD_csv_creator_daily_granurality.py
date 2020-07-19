'''
---------------------------------------------------------------------------------------------------
THIS SCRIPT IS AN INTERMEDIATE ONE, IT IS NOT PART OF THE FINAL OUTPUT. IT HAS BEEN USED IN ORDER
TO GATHER INSIGHTS ABOUT THE COLLECTED DATA DURING THE EXPLORATORY DATA ANALYSIS
---------------------------------------------------------------------------------------------------

This script together with the others of the series CD_csv_creator_*.py were used in order to
generate .csv files used for the networks plotted using Gephi.
In particular, this script generate a csv fromatted like this:
brand,users
x,y;z;a;b;...
...

'''

import os
import zipfile
import json
from json import JSONDecodeError

import matplotlib.pyplot as plt
import BrandsInfo
from datetime import datetime
import csv

cwd = os.getcwd()
IGDataFolder = os.path.join(cwd, "..\..\IGData\Brands")

# use this variable to decide what data group to analyze
NY = True

if NY:
    NYData = os.path.join(IGDataFolder, "NY")
    starting_date = datetime.strptime("04_02_2020", "%d_%m_%Y")
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


effectiveness_map = {}
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
            username = jsonFile["username"]
            if username in (BrandsInfo.NYbrands if NY else BrandsInfo.MIbrands):
                new_media_set = set([media["media_id"] for media in jsonFile["media_list"]])
                new_username_value = {"date": current_date, "media_set": new_media_set}
                if username in effectiveness_map:
                    old_username_value = effectiveness_map[username].pop()
                    old_media_set = old_username_value["media_set"]
                    old_date = old_username_value["date"]
                    dates.append(old_date)
                    new_posts = list(new_media_set.difference(old_media_set))
                    reached_accounts = []
                    for media in jsonFile["media_list"]:
                        if media["media_id"] in new_posts:
                            reached_accounts.extend(media["likers"])
                    reached_accounts = set(reached_accounts)
                    effectiveness_map[username].append({"date": old_date, "reached_accounts": list(reached_accounts)})
                    effectiveness_map[username].append(new_username_value)
                else:
                    effectiveness_map[username] = [new_username_value]


x = range(len(effectiveness_map))
new_x = [4*i for i in x]
dates = set(dates)
dates = sorted(list(dates))
cumulative_eff_map_csv = {}
for date in dates:
    plt.figure(figsize=(10, 10))
    users = []
    tmp_eff_map_csv = []
    for key,value in effectiveness_map.items():
        for dict in value:
            if dict["date"] == date:
                tmp_eff_map_csv.append({"brand": key, "users": ";".join(dict["reached_accounts"])})
                old_set = set()
                if key in cumulative_eff_map_csv.keys():
                    old_set = cumulative_eff_map_csv[key]

                old_set.update(set(dict["reached_accounts"]))
                cumulative_eff_map_csv[key] = old_set

    if NY:
        daily_csv_filename = "NY_brands_"
        cumulative_csv_filename = "NY_brands_cumulative_"
    else:
        daily_csv_filename = "MI_brands_"
        cumulative_csv_filename = "MI_brands_cumulative_"

    daily_csv_filename = daily_csv_filename + datetime.strftime(date, "%d_%m_%Y") + ".csv"
    cumulative_csv_filename = cumulative_csv_filename + datetime.strftime(date, "%d_%m_%Y") + ".csv"

    with open(daily_csv_filename, 'w') as csvfile:
        fieldnames = ['brand', 'users']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        for dicti in tmp_eff_map_csv:
            writer.writerow(dicti)

    with open(cumulative_csv_filename, 'w') as csvfile:
        fieldnames = ['brand', 'users']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        for dicti in cumulative_eff_map_csv.items():
            users = ";".join(dicti[1])
            n_dict = {"brand": dicti[0], "users": users}
            writer.writerow(n_dict)
