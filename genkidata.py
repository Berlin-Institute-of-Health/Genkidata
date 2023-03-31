# -*- coding: utf-8 -*-
import requests
from getpass import getpass
import asyncio
import aiohttp
from requests.auth import HTTPBasicAuth
import json
import random
import os

base_url = "http://localhost:8080/ehrbase/rest/openehr/v1"
username = "myuser"
password = "myPassword432"
header = {'Content-type': 'application/json;', 'Accept': 'application/json;', 'charset': 'utf-8;',
          'Prefer': 'return=representation'}
ehr_ids = []


class Composition:
    def __init__(self, amount, composition_json, ehr_id):
        self.amount = amount
        self.composition_json = composition_json
        self.ehr_id = ehr_id


async def send_ehrs(auth, ehr_count):
    async with aiohttp.ClientSession(auth=auth) as session:
        post_tasks = []
        # prepare the coroutines that post
        async for x in make_numbers(ehr_count):
            post_tasks.append(do_ehr_posts(session, base_url, x))
        # now execute them all at once
        await asyncio.gather(*post_tasks)


async def make_numbers(ehr_count):
    for i in range(0, ehr_count):
        yield i


async def do_ehr_posts(session, url, x):
    async with session.post(url + "/ehr", data="", headers=header) as response:
        data = await response.text()
        print("-> Created account number %d" % x)
        json_object = json.loads(data)
        ehr_ids.append(json_object["ehr_id"]["value"])


async def send_compositions(auth, composition_count):
    async with aiohttp.ClientSession(auth=auth) as session:
        post_tasks = []
        # prepare the coroutines that post
        async for x in make_numbers(composition_count):
            post_tasks.append(do_ehr_posts(session, base_url, x))
        # now execute them all at once
        await asyncio.gather(*post_tasks)


async def do_composition_posts(session, url, x):
    async with session.post(url + "/ehr", data="", headers=header) as response:
        data = await response.text()
        print("-> Created account number %d" % x)
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
    # base_url = input("Hey lad, please enter the Url of your openEHRAPI e.g. http://localhost:8080/ehrbase/rest/openehr/v1: ")
    # username = input("Enter you username")
    # password = getpass()
    pass


def create_ehrs(auth, ehr_count):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_ehrs(auth, ehr_count))
    finally:
        loop.close()


def create_compositions(auth, ehr_count):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_compositions(auth, ehr_count))
    finally:
        loop.close()


def generate_random_amounts(n, total):
    dividers = sorted(random.sample(range(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def count_composition_files():
    files = 0
    for _, dirnames, filenames in os.walk('./Compositions/'):
        # ^ this idiom means "we won't be using this value"
        files += len(filenames)
    return files


def load_compositions(composition_count):
    composition_file_count = count_composition_files()
    print(generate_random_amounts(composition_file_count, composition_count))


def main():
    enter_login()
    status_code = check_connection()
    while (status_code != True):
        enter_login()
    # ehr_count = input("how much EHRs do you want:")
    # composition_count = input("how much Compositions do you want:")
    ehr_count = 1
    composition_count = 20
    auth = aiohttp.BasicAuth(login=username, password=password, encoding='utf-8')
    create_ehrs(auth, ehr_count)
    load_compositions(composition_count)
    #create_compositions(auth, composition_count)


if __name__ == "__main__":
    main()
