import requests
import json

def search_plantbook(species, token):
    url = "https://open.plantbook.io/api/v1/plant/detail/{}".format(species)
    headers = {"Authorization": "Token {}".format(token)}
    result = requests.get(url, headers=headers)
    res = result.json()
    return res

def get_plantbook(alias, token): # Search unofficial name to get Scientific name
    url = "https://open.plantbook.io/api/v1/plant/search?limit=1000&alias={}".format(alias)
    headers = {"Authorization": "Token {}".format(token)}
    result = requests.get(url, headers=headers)
    name = result.json()
    return name

def get_plantbook_token(client_id, secret):
    url =  'https://open.plantbook.io/api/v1/token/'
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': secret
    }
    result = requests.post(url, data=data)
    token = result.json().get('access_token')
    return token

def get_moist(searchstring):
    search_res = get_plantbook(searchstring, config['token'])
    if search_res['results'] == []:
        moist = -1
    else:
        PID = search_res['results'][0]['pid']
        info = search_plantbook(PID, config['token'])
        max_soil_moist = info['max_soil_moist']
        min_soil_moist = info['min_soil_moist']

        moist = [min_soil_moist, max_soil_moist]

    return moist

def get_temp(searchstring):
    search_res = get_plantbook(searchstring, config['token'])
    if search_res['results'] == []:
        temp = -1
    else:
        PID = search_res['results'][0]['pid']
        info = search_plantbook(PID, config['token'])
        max_temp = info['max_temp']
        min_temp = info['min_temp']
        temp = [min_temp, max_temp]

    return temp

with open('config.json', 'r') as f:
    # Load the JSON data from the file
    config = json.load(f)