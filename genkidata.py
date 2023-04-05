import requests
import asyncio
import aiohttp
from requests.auth import HTTPBasicAuth
import json
import random
import os
from getpass import getpass

# base_url = "http://localhost:8080/ehrbase/rest/openehr/v1"
# username = "myuser"
# password = "myPassword432"

header = {'Content-type': 'application/json;', 'Accept': 'application/json;', 'charset': 'utf-8;',
          'Prefer': 'return=representation'}
headerOpts = {'Content-type': 'application/xml;', 'charset': 'utf-8;',
              'Prefer': 'return=representation'}
ehr_ids = []
successfull_compositions = {}
counter_successful = 0
global base_url
global username
global password


class Composition:
    def __init__(self, amount, composition_json, ehr_id, filename):
        self.amount = amount
        self.composition_json = composition_json
        self.ehr_id = ehr_id
        self.filename = filename


async def send_ehrs(auth, ehr_count):
    async with aiohttp.ClientSession(auth=auth) as session:
        post_tasks = []
        async for execution_counter in make_numbers(ehr_count):
            post_tasks.append(do_ehr_posts(session, execution_counter))
        await asyncio.gather(*post_tasks)


async def make_numbers(ehr_count):
    for i in range(0, ehr_count):
        yield i


async def do_ehr_posts(session, execution_counter):
    async with session.post(base_url + "/ehr", data="", headers=header) as response:
        data = await response.text()
        print("-> Created EHRs %d" % execution_counter)
        json_object = json.loads(data)
        ehr_ids.append(json_object["ehr_id"]["value"])
        print(ehr_ids)


def check_connection():
    auth_request = HTTPBasicAuth(username, password)
    response = (requests.get(base_url + "/definition/template/adl1.4", auth=auth_request))
    if response.status_code == 200:
        print("Connected successfully")
        return True
    else:
        print("Connection error:" + str(response.content) + "retry !")
        return False


def enter_login():
    global base_url
    base_url = input(
        "Hey lad, please enter the URL of your openEHR API e.g. http://localhost:8080/ehrbase/rest/openehr/v1: ")
    global username
    username = input("Enter you username: ")
    global password
    password = getpass()
    pass


def create_ehrs(auth, ehr_count):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_ehrs(auth, ehr_count))
    except:
        pass


async def send_compositions(auth, compositions):
    async with aiohttp.ClientSession(auth=auth) as session:
        post_tasks = []
        # prepare the coroutines that post
        async for x in make_numbers(len(compositions)):
            post_tasks.append(send_composition(session, compositions[x]))
        # now execute them all at once
        await asyncio.gather(*post_tasks)


async def send_composition(session, composition):
    post_tasks = []
    async for execution_counter in make_numbers(composition.amount):
        post_tasks.append(do_composition_posts(session, composition, execution_counter))
    # now execute them all at once
    await asyncio.gather(*post_tasks)


async def do_composition_posts(session, composition, execution_counter):
    data = json.dumps(composition.composition_json)
    async with session.post(base_url + "/ehr/" + composition.ehr_id + "/composition", data=data.encode("utf-8"),
                            headers=header) as response:
        data = await response.text()
        if (response.ok):
            print("-> Created composition " + composition.filename + " number %d" % execution_counter)
            successfull_compositions[composition.filename] += 1
            global counter_successful
            counter_successful = counter_successful + 1
        else:
            print("ERROR: ", response.status)
            print("Filename: ", composition.filename)
            print("Error message: ", data)


def create_compositions(auth, composition_count):
    compositions = load_compositions(composition_count)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_compositions(auth, compositions))
    finally:
        loop.close()


def generate_random_amounts(composition_file_count, composition_count):
    while composition_file_count >= composition_count:
        print("Amount of compositions needs to be bigger then: " + str(composition_file_count) + ".")
        composition_count = int(input("How much compositions do you want: "))
    dividers = sorted(random.sample(range(1, composition_count), composition_file_count - 1))
    return [a - b for a, b in zip(dividers + [composition_count], [0] + dividers)]


def count_composition_files():
    files = 0
    for _, dirnames, filenames in os.walk('compositions/'):
        files += len(filenames)
    return files


def load_compositions(composition_count):
    composition_file_count = count_composition_files()
    amounts = generate_random_amounts(composition_file_count, composition_count)
    compositions = []
    print("Loading Composition files ...")
    for root, dirs, files in os.walk("compositions", topdown=False):
        for filename in files:
            with open(os.path.join(root, filename)) as file:
                print(filename)
                compositions.append(Composition(int(amounts.pop(0)), json.load(file), random.choice(ehr_ids), filename))
                successfull_compositions[filename] = 0
    return compositions


def send_opts(filename, basic_auth_requests):
    response = requests.post(base_url + "/definition/template/adl1.4", data=open(filename).read().encode('utf8'),
                             headers=headerOpts, auth=basic_auth_requests)
    print("Upload " + filename + ": " + str(response.status_code))


def load_opts(basic_auth_requests):
    print("---------Uploading OPTS-------------")
    for root, dirs, files in os.walk("opts", topdown=False):
        for name in files:
            send_opts(os.path.join(root, name), basic_auth_requests)


def main():
    enter_login()
    status_code = check_connection()
    while not status_code:
        enter_login()
        status_code = check_connection()
    basic_auth_requests = HTTPBasicAuth(username, password)
    auth = aiohttp.BasicAuth(login=username, password=password, encoding='utf-8')
    load_opts(basic_auth_requests)
    print("---------Configure Amount-------------")
    ehr_count = int(input("How much EHRs do you want: "))
    composition_count = int(input("How much compositions do you want: "))
    print("---------Creating EHRs-------------")
    create_ehrs(auth, ehr_count)
    print("---------Creating Compositions-------------")
    create_compositions(auth, composition_count)
    print("Successfully created: " + str(successfull_compositions))
    print("Sum of successfully created: " + str(counter_successful))


if __name__ == "__main__":
    main()

# ['93019b6a-d493-429a-b7fd-d4b7b0bc4535']
