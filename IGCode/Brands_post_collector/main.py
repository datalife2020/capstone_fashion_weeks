"""
The purpose of this script is to acquire data from instagram, based on user-profile ids.

In order to let it work, a secrets.txt file is needed inside the input folder. This file must contain the credentials
of the IG users to be used for the data collection in the following format:
username:password

Another file must be provided in the input folder: userids_to_analyse.json. This file must contain the user id of the
user profile to be analised as a JSON array in the following format:
[{"username": "username1", "user_id": "userid1"}, {"username": "username2", "user_id": "userid2"}]
For more info about this, have a look to the username_to_userid.py script.

"""
import itertools
import os
import json
import sys
import instabot
from random import randint
import datetime
import time


## util functions definition

def write_json(daxta, strxing, filenames):
    if os.path.exists(filenames) is False:
        with open(filenames, 'w') as outfile:
            json.dump({"checked": []}, outfile, indent=4)
    with open(filenames, "r+") as jsonFile:
        data = json.load(jsonFile)
        tmp = data[daxta]
        data[daxta] = strxing
        jsonFile.seek(0)  # rewind
        json.dump(data, jsonFile, indent=4)
        jsonFile.truncate()


def read_json(reaxd, filenames):
    if os.path.exists(filenames) is False:
        with open(filenames, 'w') as outfile:
            json.dump({"checked": []}, outfile, indent=4)
    with open(filenames) as f:
        data = json.load(f)
    loplop = data[reaxd]
    xyz = {'me': loplop}
    return xyz

def rr_from_secrets(pathToSecrets):
    accounts = []
    # creates a list which enable to pick accounts from which performing requests
    with open(pathToSecrets) as secrets:
        for line in secrets:
            username, password = line.split(':')
            accounts.append({"username": username, "password": password})

    # access it through next(account_rr) in a round-robin fashion, the function returns also the number of accounts
    # so that it is possible to check whether we have logged in in all of them
    return itertools.cycle(accounts), len(accounts)

## end of util functions definition

useridsFile = 'userids_to_analyse.json'
inputPath = 'input'
utilsPath = 'f_utils'
secretsFile = 'secrets.txt'
out = 'output'
now = datetime.datetime.now()
log = 'log_' + str(now.strftime("%d_%m_%Y")) + '.txt'

# create a f_utils folder, used to store inside it some utils file (e.g., logs and the checked.json file)
if os.path.exists(utilsPath) == False:
    os.mkdir(utilsPath)

with open(os.path.join(utilsPath, log), 'w') as logging:
    logging.write(str(datetime.datetime.now()) + '>>> Starting the collection at time ' + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n')

# create the media_for_brands folder. It will contain json files named as userids. Each of them contains the list of posts
# that should be analysed for each userids. These lists of posts are updated at each run, adding newer posts that have been posted
# since the last run.
mediaBrandsFolder = 'media_for_brands'
if os.path.exists(mediaBrandsFolder) == False:
    os.mkdir(mediaBrandsFolder)

accounts_rr, accounts_no = rr_from_secrets(os.path.join(inputPath,secretsFile))

with open(os.path.join(inputPath, useridsFile), 'r') as userids:
    userToAnalyse = json.load(userids)
if userToAnalyse == []:
    print('no users')
    exit()

# create a list of only userids
input = []
for item in userToAnalyse:
    try:
        input.append(item['user_id'])
    except:
        e = sys.exc_info()
        print(e)

bot = instabot.Bot()
botAccount = next(accounts_rr)
with open(os.path.join(utilsPath,log), 'a') as logging:
    logging.write(str(datetime.datetime.now()) + '>>> Connecting with ' + botAccount["username"] + '\n')

bot.login(username=botAccount["username"], password=botAccount["password"])
for i in input:
    mediasToWrite = set()
    if os.path.exists(os.path.join(mediaBrandsFolder, i + '.json')) == False:
        with open(os.path.join(mediaBrandsFolder, i + '.json'), "w") as jsonFile:
            json.dump({"media_id_list": []}, jsonFile)
    else:
        with open(os.path.join(mediaBrandsFolder, i + '.json'), "r") as jsonFile:
            mediasToWrite = set(json.load(jsonFile)["media_id_list"])

    softBanNumber = 0
    while True:
        try:
            user_medias = bot.get_last_user_medias(i, 15)
            break
        except Exception as e:
            if e.args[0] == 'SoftBan':
                print("####################### A soft ban exception has been catched, changing bot...")
                bot.logout()
                softBanNumber += 1
                if softBanNumber == accounts_no:
                    randx = randint(1000, 1800)
                    with open(os.path.join(utilsPath, log), 'a') as logging:
                        logging.write(str(datetime.datetime.now()) + '>>> All the available accounts have been soft banned. Sleeping for' + str(randx) + " seconds..." + '\n')
                    print("####################### All the available accounts have been soft banned. Sleeping for " + str(randx) + " seconds...")
                    time.sleep(randx)
                    softBanNumber = 0
                botAccount = next(accounts_rr)
                with open(os.path.join(utilsPath, log), 'a') as logging:
                    logging.write(str(
                        datetime.datetime.now()) + '>>> Current account softbanned. Connecting with ' + botAccount["username"] + '\n')
                randx = randint(5, 10)
                time.sleep(randx)
                bot.login(username=botAccount["username"], password=botAccount["password"])

    for el in user_medias:
        mediasToWrite.add(el)
    with open(os.path.join(mediaBrandsFolder, i + '.json'), "w") as jsonFile:
        json.dump({"media_id_list": list(mediasToWrite)}, jsonFile)

    randx = randint(1, 5)
    time.sleep(randx)

with open(os.path.join(utilsPath, log), 'a') as logging:
    logging.write(str(datetime.datetime.now()) + '>>> The medias id have been acquired. Now the core of the script will start...\n')
print("####################### The medias id have been acquired. Now the core of the script will start...")

if os.path.exists(out) == False:
    os.mkdir(out)

checked = read_json("checked", os.path.join(utilsPath, 'checked.json'))
checked = checked['me']

## Check if files exist (checked.json and invalid.txt)
if os.path.exists(os.path.join(utilsPath, 'checked.json')) is False:
    with open(os.path.join(utilsPath, 'checked.json'), "w") as make_checked:
        make_checked.write({"checked": []})
if os.path.exists(os.path.join(utilsPath, 'invalid.txt')) == False:
    with open(os.path.join(utilsPath, 'invalid.txt'), "w") as make_inv:
        make_inv.write('')

todaysDir = os.path.join(out, str(now.strftime("%d_%m_%Y")))
if os.path.exists(todaysDir) == False:
    os.mkdir(todaysDir)

for i in input:
    if i in checked or i == " " or i == "":
        with open(os.path.join(utilsPath, log), 'a') as logging:
            logging.write(str(datetime.datetime.now()) + '>>> ' + 'Skipping ' + i + '\n')
    else:
        with open(os.path.join(utilsPath, log), 'a') as logging:
            logging.write(str(
                datetime.datetime.now()) + '>>> Analysing user: ' + i + '\n')
        print('#######################  ANALYSING USER: ' + i)
        softBanNumber = 0
        while True:
            try:
                info = bot.get_user_info(i)
                break
            except Exception as e:
                if e.args[0] == 'SoftBan':
                    print("####################### A soft ban exception has been catched, changing bot...")
                    bot.logout()
                    softBanNumber += 1
                    if softBanNumber == accounts_no:
                        randx = randint(1000, 1800)
                        with open(os.path.join(utilsPath, log), 'a') as logging:
                            logging.write(str(datetime.datetime.now()) + '>>> All the available accounts have been soft banned. Sleeping for' + str(randx) + " seconds..." + '\n')
                        print("####################### All the available accounts have been soft banned. Sleeping for " + str(randx) + " seconds...")
                        time.sleep(randx)
                        softBanNumber = 0
                    botAccount = next(accounts_rr)
                    with open(os.path.join(utilsPath, log), 'a') as logging:
                        logging.write(str(datetime.datetime.now()) + '>>> Current account softbanned. Connecting with ' + botAccount["username"] + '\n')
                    randx = randint(5, 10)
                    time.sleep(randx)
                    bot.login(username=botAccount["username"], password=botAccount["password"])

        if info == False:
            print("invalid.")
            with open(os.path.join(utilsPath, log), 'a') as logging:
                logging.write(str(datetime.datetime.now()) + '>>> ' + 'Account ' + i + ' is in invalid.' + '\n')
            with open(os.path.join(utilsPath, 'invalid.txt'), 'a') as invalids:
                invalids.write(i + '\n')
        else:
            json_format = json.dumps(info)
            json1_data = json.loads(json_format)
            if info['is_private'] == True:
                with open(os.path.join(utilsPath, log), 'a') as logging:
                    logging.write(str(datetime.datetime.now()) + '>>> ' + i + ' is private.' + '\n')
            if info['is_private'] == False:
                with open(os.path.join(utilsPath, log), 'a') as logging:
                    logging.write(str(datetime.datetime.now()) + '>>> ' + i + ' is public.' + '\n')

                # get all the ids of the user media
                with open(os.path.join(mediaBrandsFolder, i + '.json'), "r") as jsonFile:
                    medias = set(json.load(jsonFile)["media_id_list"])
                media_list = []
                for media in medias:
                    with open(os.path.join(utilsPath, log), 'a') as logging:
                        logging.write(str(
                            datetime.datetime.now()) + '>>> Getting information of media ' + media + ' of account ' + i + '\n')
                    randx = randint(2, 10)
                    time.sleep(randx)
                    softBanNumber = 0
                    while True:
                        try:
                            likers = bot.get_media_likers(media)
                            randx = randint(1, 5)
                            time.sleep(randx)
                            url_media = bot.get_link_from_media_id(media)
                            randx = randint(1, 5)
                            time.sleep(randx)
                            commenters = bot.get_media_commenters(media)
                            break
                        except Exception as e:
                            if e.args[0] == 'SoftBan':
                                print("####################### A soft ban exception has been catched, changing bot...")
                                bot.logout()
                                softBanNumber += 1
                                if softBanNumber == accounts_no:
                                    randx = randint(1000, 1800)
                                    with open(os.path.join(utilsPath, log), 'a') as logging:
                                        logging.write(str(datetime.datetime.now()) + '>>> All the available accounts have been soft banned. Sleeping for' + str(randx) + " seconds..." + '\n')
                                    print("####################### All the available accounts have been soft banned. Sleeping for " + str(randx) + " seconds...")
                                    time.sleep(randx)
                                    softBanNumber = 0
                                botAccount = next(accounts_rr)
                                with open(os.path.join(utilsPath, log), 'a') as logging:
                                    logging.write(str(
                                        datetime.datetime.now()) + '>>> Current account softbanned. Connecting with ' +
                                                  botAccount["username"] + '\n')
                                randx = randint(5, 10)
                                time.sleep(randx)
                                bot.login(username=botAccount["username"], password=botAccount["password"])

                    media_list.append({"media_id": media, "media_url": url_media, "likers": likers, "commenters": commenters})
                json1_data.update({"media_list": media_list})
            tree = [{i: json1_data}]

            with open('{}/'.format(todaysDir) + i + '.json', 'w') as fp:
                json.dump(tree, fp, indent=4)

        # appending to checked.json because the user id i has been analysed
        checked.append(i)
        write_json('checked', checked, os.path.join(utilsPath, 'checked.json'))
        if info['is_private'] == False:
            with open(os.path.join(utilsPath, log), 'a') as logging:
                logging.write(str(datetime.datetime.now()) + '>>> User ' + i + ' analysed successfully.' + '\n')

        randx = randint(20, 50)
        time.sleep(randx)

bot.logout()

with open(os.path.join(utilsPath, log), 'a') as logging:
    logging.write(str(datetime.datetime.now()) + '>>> Collection ended at time ' + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n')