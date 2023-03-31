# -*- coding: utf-8 -*-
from xml.etree import ElementTree

import requests
from getpass import getpass
import asyncio
import aiohttp
from requests.auth import HTTPBasicAuth
import json
import random
import os

#base_url = "http://localhost:8080/ehrbase/rest/openehr/v1"
#username = "myuser"
# password = "myPassword432"

header = {'Content-type': 'application/json;', 'Accept': 'application/json;', 'charset': 'utf-8;',
          'Prefer': 'return=representation'}
headerOpts = {'Content-type': 'application/xml;', 'Accept': 'application/json;', 'charset': 'utf-8;',
              'Prefer': 'return=representation'}
ehr_ids = []
compositions = []
successfull = 0
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
        # prepare the coroutines that post
        async for x in make_numbers(ehr_count):
            post_tasks.append(do_ehr_posts(session, x))
        # now execute them all at once
        await asyncio.gather(*post_tasks)


async def make_numbers(ehr_count):
    for i in range(0, ehr_count):
        yield i


async def do_ehr_posts(session, x):
    async with session.post(base_url + "/ehr", data="", headers=header) as response:
        data = await response.text()
        print("-> Created EHRs %d" % x)
        json_object = json.loads(data)
        ehr_ids.append(json_object["ehr_id"]["value"])


def check_connection():
    authRequests = HTTPBasicAuth(username, password)
    response = (requests.get(base_url + "/definition/template/adl1.4", auth=authRequests))
    if response.status_code == 200:
        print("Connected successfully")
        return True
    else:
        print("Connection error:" + str(response.text))
        return False


def enter_login():
    global base_url
    base_url = input("Hey lad, please enter the Url of your openEHRAPI e.g. http://localhost:8080/ehrbase/rest/openehr/v1: ")
    global username
    username = input("Enter you username: ")
    global password
    password = getpass()


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
    async for x in make_numbers(composition.amount):
        post_tasks.append(do_composition_posts(session, composition, x))
    # now execute them all at once
    await asyncio.gather(*post_tasks)


async def do_composition_posts(session, composition, x):
    data = json.dumps(composition.composition_json)
    async with session.post(base_url + "/ehr/"+composition.ehr_id+"/composition", data=data.encode("utf-8"), headers=header) as response:
        data = await response.text()
        print("-> Created composition "+ composition.filename+" number %d" % x)


def create_compositions(auth, composition_count):
    compositions = load_compositions(composition_count)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_compositions(auth, compositions))
    finally:
        loop.close()


def generate_random_amounts(n, total):
    dividers = sorted(random.sample(range(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def count_composition_files():
    files = 0
    for _, dirnames, filenames in os.walk('./Compositions/'):
        files += len(filenames)
    return files


def load_compositions(composition_count):
    composition_file_count = count_composition_files()
    amounts = generate_random_amounts(composition_file_count, composition_count)
    compositions = []
    print("Loading Composition files ...")
    for root, dirs, files in os.walk("./Compositions", topdown=False):
        for filename in files:
            with open(os.path.join(root, filename)) as file:
                compositions.append(Composition(int(amounts.pop(0)), json.load(file), random.choice(ehr_ids), filename))
    return compositions


def send_opts(filename, basic_auth_requests):
    response = requests.post(base_url + "/definition/template/adl1.4", data=open(filename).read().encode('utf8'),
                             headers=headerOpts, auth=basic_auth_requests)
    print("Upload: " + str(response.json()))


def load_opts(basic_auth_requests):
    print("---------Uploading OPTS-------------")
    for root, dirs, files in os.walk("./Opts", topdown=False):
        for name in files:
            send_opts(os.path.join(root, name), basic_auth_requests)


def main():
    enter_login()
    status_code = check_connection()
    while (status_code != True):
        enter_login()
    basic_auth_requests = HTTPBasicAuth(username, password)
    auth = aiohttp.BasicAuth(login=username, password=password, encoding='utf-8')
    load_opts(basic_auth_requests)
    ehr_count = int(input("how much EHRs do you want: "))
    composition_count = int(input("how much Compositions do you want: "))
    create_ehrs(auth, ehr_count)
    create_compositions(auth, composition_count)


# create_compositions(auth, composition_count)


if __name__ == "__main__":
    main()
