import itertools
import inspect
import time
import json
from configobj import ConfigObj
import os

def rr_from_secrets(pathToSecrets):
    accounts = []
    # creates a list which enable to pick accounts from which performing requests
    with open(pathToSecrets) as secrets:
        for line in secrets:
            username, password = line.split(':')
            password = password.replace('\n', '')
            accounts.append({"username": username, "password": password})

    # access it through next(account_rr) in a round-robin fashion, the function returns also the number of accounts
    # so that it is possible to check whether we have logged in in all of them
    return itertools.cycle(accounts), len(accounts)


def get_brands_from_json(pathToJson, pathToConfig):
    brands_list = []
    with open(pathToJson) as json_file:
        json_array = json.load(json_file)
        for json_object in json_array:
            brands_list.append(json_object["username"])
    return brands_list


def get_users_from_brand_name(brand_name, path_to_json):
    users = []
    with open(path_to_json) as json_file:
        json_array = json.load(json_file)
        for dict in json_array:
            if brand_name == dict["username"]:
                return dict["reached_accounts"]


def create_config_file(pathToConfig):
    if not os.path.exists(pathToConfig):
        config = ConfigObj()
        config.filename = pathToConfig
        config.write()


def update_config_property(pathToConfig, property, value):
    config = ConfigObj(pathToConfig)
    config[property] = value
    config.write()


def read_config_property(pathToConfig, property):
    config = ConfigObj(pathToConfig)
    return config[property]


def DebugLogger(msg, bot):
    calframe = inspect.getouterframes(inspect.currentframe(), 2)
    callerFunction = calframe[1][3]
    with open("debug.log", "a+") as d:
        d.write("{0} - [{1}]: {2}\n".format(time.strftime("%d/%m - %H:%M:%S"), callerFunction, msg))

    bot.logger.debug("[{0}]: {1}".format(callerFunction, msg))

def prepare_output_file(output_file, file_counter):
    if not os.path.exists(output_file.format(file_counter)):
        with open(output_file.format(file_counter), 'a+') as fout:
            fout.write("[")


def store_user(path, user_info, file_counter, file_content_counter, file_content_limit, bot):
    fout = open(path.format(file_counter), "a+")

    fout.close()
