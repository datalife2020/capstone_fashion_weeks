'''
---------------------------------------------------------------------------------------------------
THIS SCRIPT IS AN INTERMEDIATE ONE, IT IS NOT PART OF THE FINAL OUTPUT. IT HAS BEEN USED IN ORDER
TO GATHER INSIGHTS ABOUT THE COLLECTED DATA DURING THE EXPLORATORY DATA ANALYSIS
---------------------------------------------------------------------------------------------------

This script generate several barcharts showing how many users have been reached with success for each
brand during the FWs. The number of barcharts generated depend on the number of days of the FW, which
varies between New York and Milan.
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
NY = False

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

for date in dates:
    plt.figure(figsize=(10, 10))
    users = []
    tmp_eff_map = {}
    tmp_eff_map_csv = []
    for key,value in effectiveness_map.items():
        for dict in value:
            if dict["date"] == date:
                #users.append(key)
                tmp_eff_map[key] = len(dict["reached_accounts"])
                tmp_eff_map_csv.append({"brand": key, "users": dict["reached_accounts"]})

    tmp_eff_map = {k:v for k,v in sorted(tmp_eff_map.items(), key=lambda x:x[1])}

    i = 0
    for key, value in tmp_eff_map.items():
        if datetime.strptime((BrandsInfo.NYBrandsExDate[key] if NY else BrandsInfo.MIBrandsExDate[key]), "%d-%m-%Y") == date:
            plt.barh(new_x[i], value, height=3, color='r')
        else:
            plt.barh(new_x[i], value, height=3, color='b')
        i = i + 1
    plt.yticks(new_x, tmp_eff_map.keys(), rotation="horizontal", size='small')
    plt.xlabel("Accounts reached")
    plt.title("Accounts number reached with success - computed between " + date.strftime("%d/%m/%Y") + " and " +
              date.replace(day=date.day+1).strftime("%d/%m/%Y"))
    if NY:
        barchart_name = "NY_barchart_"
    else:
        barchart_name = "MI_barchart_"

    plt.savefig(barchart_name + date.strftime("%d_%m_%Y") + ".pdf", bbox_inches='tight', format="pdf")
    plt.show()
