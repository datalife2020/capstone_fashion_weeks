"""
This script is used to convert usernames to userids, in order to use them in the main.py script.
The usernames to be converted must be written in a usernames_to_analyse.txt file located in the input folder.
The format must be as follows:
username1
username2
...

The output will be stored in the userids_to_analyse.json as a JSON array in the followind format:
[{"username": "username1", "user_id": "userid1"}, {"username": "username2", "user_id": "userid2"}]

"""
import instabot
import json
import os
import itertools

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

cwd = os.getcwd()
inputFolder = os.path.join(cwd, 'input')

usernamesFile = 'usernames_to_analyse.txt'
useridsFile = 'userids_to_analyse.json'
secretsFile = 'secrets.txt'

bot = instabot.Bot()

accounts_rr, accounts_no = rr_from_secrets(os.path.join(inputFolder, secretsFile))

botAccount = next(accounts_rr)
bot.login(username=botAccount["username"], password=botAccount["password"])

usernamesPath = os.path.join(inputFolder, usernamesFile)
useridsPath = os.path.join(inputFolder, useridsFile)

with open(usernamesPath, 'r') as usernames:
    with open (useridsPath, 'w+') as userids:
        jsonObjects = []
        for username in usernames:
            username = username.replace('\n', '')
            userid = bot.get_user_id_from_username(username)
            info = {"username":username, "user_id": userid}
            jsonObjects.append(info)
        json.dump(jsonObjects, userids)

bot.logout()