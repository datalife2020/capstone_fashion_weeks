'''
---------------------------------------------------------------------------------------------------
THIS SCRIPT IS AN INTERMEDIATE ONE, IT IS NOT PART OF THE FINAL OUTPUT. IT HAS BEEN USED IN ORDER
TO GATHER INSIGHTS ABOUT THE COLLECTED DATA DURING THE EXPLORATORY DATA ANALYSIS
---------------------------------------------------------------------------------------------------

This script is used to print one barchart for each fashion week in which two variables are associated
with each brand: avg reached accounts and avg followers count.
This has been used in order to understand whether there was a correlation between the number of reached
accounts and the number of followers.
'''

import os
import zipfile
import json
from json import JSONDecodeError
from operator import itemgetter

import matplotlib.pyplot as plt
import BrandsInfo
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages


cwd = os.getcwd()
IGDataFolder = os.path.join(cwd, "..\..\IGData\Brands")

# use this variable to decide what data group to analyze
NY = True

# use this variable to decide the best "plot_first" brands to plot, used for readability reason.
# 0 to plot every brand
plot_first = 20

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
                followers_count = jsonFile["follower_count"]
                # media_count = jsonFile["media_count"]
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
                    effectiveness_map[username].append({"date": old_date, "reached_accounts": len(reached_accounts), "followers_count": followers_count})
                    effectiveness_map[username].append(new_username_value)
                else:
                    effectiveness_map[username] = [new_username_value]


if plot_first:
    x = range(plot_first)
else:
    x = range(len(effectiveness_map))

new_x = [12*i for i in x]
dates = set(dates)

plt.figure(figsize=(13, 10))
users = []
for key,value in effectiveness_map.items():
    avg_reached_accounts = 0
    avg_followers_count = 0
    value.pop()
    users.append(key)
    for dict in value:
        avg_reached_accounts = avg_reached_accounts + int(dict["reached_accounts"])
        avg_followers_count = avg_followers_count + int(dict["followers_count"])
    avg_reached_accounts = avg_reached_accounts/len(value)
    avg_followers_count = avg_followers_count/len(value)
    effectiveness_map[key] = {"avg_reached_accounts": avg_reached_accounts, "avg_followers_count": avg_followers_count}

effectiveness_map = {k:v for k,v in sorted(effectiveness_map.items(), key=lambda x:x[1]["avg_reached_accounts"])}

i = 0
if plot_first:
    map_iterate = list(effectiveness_map.items())[-plot_first:]
    keys = list(effectiveness_map.keys())[-plot_first:]
else:
    map_iterate = effectiveness_map.items()
    keys = effectiveness_map.keys()

for key, value in map_iterate:
    r_a_bar = plt.barh(new_x[i], value["avg_reached_accounts"], height=3, color='b')
    f_c_bar = plt.barh(new_x[i] + 4, value["avg_followers_count"], height=3, color='g')
    plt.barh(new_x[i] + 8, 0, height=1) #add space between bar
    i = i + 1
plt.xscale("log")
plt.yticks([tick+2 for tick in new_x], keys, rotation="horizontal", size='small')
plt.legend([r_a_bar, f_c_bar], ["Average reached accounts", "Average followers count"])
title = "Average number of accounts reached with success and average followers count during the "
if NY:
    title = title + "New York"
else:
    title = title + "Milan"
title = title + " FW"
if plot_first:
    title = title + " - Best " + str(plot_first) + " brands."
plt.title(title)
plt.savefig("barchart_avg.pdf", bbox_inches='tight', format="pdf")
plt.show()
