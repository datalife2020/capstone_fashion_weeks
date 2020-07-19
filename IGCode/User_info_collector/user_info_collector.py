import random
import instabot as ib
import os
import Utils
import time
import json

users_json = "NY_users.json"
config_file = "config.ini"
secrets_file = "secrets.txt"
data_folder_name = "Data"
bio_out_filename = "user_infos_bio_{0}.json"
out_filename = "user_infos_{0}.json"
try:
    bio_file_counter = int(Utils.read_config_property(config_file, "bio_file_counter"))
except KeyError:
    bio_file_counter = 0

try:
    file_counter = int(Utils.read_config_property(config_file, "file_counter"))
except KeyError:
    file_counter = 0

try:
    bio_file_content_counter = int(Utils.read_config_property(config_file, "bio_file_content_counter"))
except KeyError:
    bio_file_content_counter = 0

try:
    file_content_counter = int(Utils.read_config_property(config_file, "file_content_counter"))
except KeyError:
    file_content_counter = 0

if not os.path.exists(data_folder_name):
    os.mkdir(data_folder_name)

# define a number of request limit for each account
request_limit = 1500
# define a statistically reasonable threshold of accounts to be analyzed
sr_user_threshold = 0.20
file_content_limit = 2000

path_to_out_bio = os.path.join(data_folder_name, bio_out_filename)
path_to_out = os.path.join(data_folder_name, out_filename)

Utils.prepare_output_file(path_to_out_bio, bio_file_counter)
Utils.prepare_output_file(path_to_out, file_counter)

# get account list in a round robin fashion
accounts_rr, accounts_no = Utils.rr_from_secrets("secrets.txt")
# get brands list to be monitored
brands_list = Utils.get_brands_from_json(users_json, config_file)
# create config file
Utils.create_config_file(config_file)


botAccount = next(accounts_rr)
bot = ib.Bot()
bot.login(username=botAccount["username"], password=botAccount["password"], ask_for_code=True)

Utils.DebugLogger("Collection started.", bot)
used_accounts = 0
request_no = 0
try:
    analyzed_brands = list(Utils.read_config_property(config_file, "analyzed_brands"))
except KeyError:
    analyzed_brands = []

new_brand = False

for brand in brands_list:
    if brand not in analyzed_brands:
        users = set(Utils.get_users_from_brand_name(brand, users_json))
        min_users_number = int(len(users)*sr_user_threshold)
        try:
            analyzed_users_bio = set(Utils.read_config_property(config_file, "analyzed_users_bio"))
        except KeyError:
            analyzed_users_bio = set()
        try:
            analyzed_users = set(Utils.read_config_property(config_file, "analyzed_users"))
        except KeyError:
            analyzed_users = set()
        try:
            bio_init_size = int(Utils.read_config_property(config_file, "bio_init_size"))
        except KeyError:
            bio_init_size = len(analyzed_users_bio)
        try:
            init_size = int(Utils.read_config_property(config_file, "init_size"))
        except KeyError:
            init_size = len(analyzed_users)

        Utils.DebugLogger("{0} users for the current brand. {1} users have been analyzed".format(len(users), len(
            analyzed_users_bio) + len(analyzed_users)), bot)
        #users = list(users.difference(analyzed_users_bio, analyzed_users))
        #Utils.DebugLogger("{0} users left after the set difference for the brand {1}".format(len(users), brand), bot)

        if new_brand:
            bio_shared_accounts = len(users.intersection(analyzed_users_bio))
            shared_accounts = len(users.intersection(analyzed_users))
            Utils.update_config_property(config_file, "bio_shared_accounts", bio_shared_accounts)
            Utils.update_config_property(config_file, "shared_accounts", shared_accounts)
        else:
            bio_shared_accounts = int(Utils.read_config_property(config_file, "bio_shared_accounts"))
            shared_accounts = int(Utils.read_config_property(config_file, "shared_accounts"))

        users = list(users)
        # this variable is useful to count also the accounts which have been picked now but that have been analyzed
        # before for another brand
        bio_skipped_accounts = 0
        skipped_accounts = 0
        while len(analyzed_users_bio) - bio_init_size + bio_shared_accounts < min_users_number:
            user = random.choice(users)
            if user in analyzed_users_bio:
                bio_skipped_accounts = bio_skipped_accounts + 1
                Utils.DebugLogger("The user {0} has already been analyzed and has the biography. Skipped {1}/{2} "
                                  "accounts for this reason".format(user, bio_skipped_accounts, bio_shared_accounts)
                                  , bot)
                users.remove(user)
            elif user in analyzed_users:
                skipped_accounts = skipped_accounts + 1
                Utils.DebugLogger("The user {0} has already been analyzed and has not the biography. Skipped {1}/{2} "
                                  "accounts for this reason ".format(user, skipped_accounts, shared_accounts)
                                  , bot)
                users.remove(user)
            else:
                Utils.DebugLogger("{0} users left for the current brand".format(len(users)), bot)
                while True:
                    try:
                        user_info = bot.get_user_info(user)
                        request_no = request_no + 1
                        Utils.DebugLogger(
                            "Total requests made with the account {0}: {1}/{2} ".format(botAccount["username"], request_no,
                                                                                        request_limit), bot)
                        if user_info:
                            if "chaining_suggestions" in user_info:
                                del user_info["chaining_suggestions"]
                            # priority to users with biography: if the user considered has no biography, store it but in a different file
                            if len(user_info["biography"]) == 0:
                                Utils.DebugLogger(
                                    "The user {0} has no biography. Number of accounts analyzed without biography for the brand {1}: {2}".format(
                                        user, brand, len(analyzed_users) - init_size + shared_accounts), bot)
                                with open(path_to_out.format(file_counter), "a+") as fout:
                                    fout.write(json.dumps(user_info, indent=4))
                                    Utils.DebugLogger("The above user has been written into {0}, written {1}/{2} elements".format(
                                        out_filename.format(file_counter), file_content_counter, file_content_limit), bot)

                                    file_content_counter = file_content_counter + 1
                                    if file_content_counter >= file_content_limit:
                                        Utils.DebugLogger("Reached the maximum number of users info in the non-biography file, changing file...", bot)
                                        fout.write("]")
                                        file_content_counter = 0
                                        file_counter = file_counter + 1
                                        Utils.prepare_output_file(path_to_out, file_counter)
                                    else:
                                        fout.write(",")
                                analyzed_users.add(user)
                                Utils.update_config_property(config_file, "analyzed_users", list(analyzed_users))
                                Utils.update_config_property(config_file, "file_content_counter", file_content_counter)
                                Utils.update_config_property(config_file, "file_counter", file_counter)
                            else:
                                Utils.DebugLogger(
                                    "The user {0} has the biography. Number of accounts analyzed with biography for the brand {1}: {2}/{3}".format(
                                        user, brand, len(analyzed_users_bio)-bio_init_size + bio_shared_accounts, min_users_number), bot)

                                with open(path_to_out_bio.format(bio_file_counter), "a+") as fout:
                                    fout.write(json.dumps(user_info, indent=4))
                                    Utils.DebugLogger("The above user has been written into {0}, written {1}/{2} elements".format(
                                        bio_out_filename.format(bio_file_counter), bio_file_content_counter, file_content_limit),
                                                      bot)
                                    bio_file_content_counter = bio_file_content_counter + 1
                                    if bio_file_content_counter >= file_content_limit:
                                        Utils.DebugLogger("Reached the maximum number of users info in the biography file, changing file...", bot)
                                        fout.write("]")
                                        bio_file_content_counter = 0
                                        bio_file_counter = bio_file_counter + 1
                                        Utils.prepare_output_file(path_to_out_bio, bio_file_counter)
                                    else:
                                        fout.write(",")
                                analyzed_users_bio.add(user)
                                Utils.update_config_property(config_file, "analyzed_users_bio", list(analyzed_users_bio))
                                Utils.update_config_property(config_file, "bio_file_content_counter", bio_file_content_counter)
                                Utils.update_config_property(config_file, "bio_file_counter", bio_file_counter)

                        users.remove(user)
                        randx = random.randint(4, 15)
                        time.sleep(randx)
                        if request_no == request_limit:
                            raise Exception('RequestLimit')
                        break
                    except Exception as e:
                        if e.args[0] == 'SoftBan':
                            Utils.DebugLogger("A soft ban exception has been catched, changing bot...", bot)
                        if e.args[0] == 'RequestLimit':
                            Utils.DebugLogger("The set request limit has been reached for the current account. Changing bot...", bot)
                        if e.args[0] == 'SoftBan' or e.args[0] == "RequestLimit":
                            bot.logout()
                            used_accounts = used_accounts + 1
                            if used_accounts == accounts_no:
                                # sleep for the night: from 6 to 8 hours with minute time granularity
                                randx = random.randint(360, 480)
                                Utils.DebugLogger(
                                    "All the accounts have exhausted their daily requests or have been soft banned. Sleeping for {0} minutes.".format(
                                        randx), bot)
                                time.sleep(60 * randx)
                                used_accounts = 0
                            botAccount = next(accounts_rr)
                            randx = random.randint(15, 30)
                            time.sleep(randx)
                            Utils.DebugLogger("Connecting with {0}...".format(botAccount["username"]), bot)
                            bot.login(username=botAccount["username"], password=botAccount["password"])
                            request_no = 0
                            user = random.choice(users)
        analyzed_brands.append(brand)
        Utils.update_config_property(config_file, "bio_init_size", len(analyzed_users_bio))
        Utils.update_config_property(config_file, "init_size", len(analyzed_users))
        Utils.update_config_property(config_file, "analyzed_brands", analyzed_brands)
    else:
        Utils.DebugLogger("Skipping brand {0} because already analyzed".format(brand), bot)
    new_brand = True
Utils.DebugLogger("Collection ended.")
bot.logout()