# This program calls the OpenFarm API to get information (sun requirement, height, spread) about a certain plant

import requests

def find_spread(query):
    # set up API endpoint and search query
    endpoint = "https://openfarm.cc/api/v1/crops/"

    # make API request and parse response
    try:
        response = requests.get(endpoint + query)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    plant_data = response.json()
    spread = plant_data['data']['attributes']['spread']
    sun_requirement = plant_data['data']['attributes']['sun_requirements']
    height = plant_data['data']['attributes']['height']
    print(f'sun_requirement: {sun_requirement}, height: {height}, spread: {spread}')

    return spread


def find_sun_requirement(query):
    # set up API endpoint and search query
    endpoint = "https://openfarm.cc/api/v1/crops/"

    # make API request and parse response
    try:
        response = requests.get(endpoint + query)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    plant_data = response.json()
    spread = plant_data['data']['attributes']['spread']
    sun_requirement = plant_data['data']['attributes']['sun_requirements']
    height = plant_data['data']['attributes']['height']
    print(f'sun_requirement: {sun_requirement}, height: {height}, spread: {spread}')

    return sun_requirement

def find_height(query):
    # set up API endpoint and search query
    endpoint = "https://openfarm.cc/api/v1/crops/"

    # make API request and parse response
    try:
        response = requests.get(endpoint + query)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    plant_data = response.json()
    spread = plant_data['data']['attributes']['spread']
    sun_requirement = plant_data['data']['attributes']['sun_requirements']
    height = plant_data['data']['attributes']['height']
    print(f'sun_requirement: {sun_requirement}, height: {height}, spread: {spread}')

    return height