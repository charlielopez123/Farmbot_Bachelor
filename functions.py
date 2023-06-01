"""
File with the definition of the functions used in the main program.

June 2023
"""

import requests
import paho.mqtt.client as mqtt
import json
import time
import numpy as np

import global_variables


# Check the current weather to fill the array with the past weather. The API provides updates every 15 minutes
def current_weather():

    # Open the json file where the password is stored
    with open("password.json", "r") as jsonfile:
        data = json.load(jsonfile)

    # Setting up the API call
    res1 = requests.get(data['url2'])
    res2 = requests.get(data['url3'])

    weather_data = res1.json()
    radiation = res2.json()

    date = radiation['dt']
    global_variables.temp_10 = radiation['t10'] - 273.15
    global_variables.temp_0 = radiation['t0'] - 273.15
    global_variables.moisture = radiation['moisture'] * 100
    print(date, global_variables.moisture)

    if global_variables.date_last_update != weather_data['current']['last_updated']:
        global_variables.date_last_update = weather_data['current']['last_updated']

        global_variables.actual_precipitation = weather_data['current']['precip_mm']

        # Fill the array by appending last value in the last position (newest) and removing the first position value (oldest)
        global_variables.past_rain.append(weather_data['current']['precip_mm'])
        global_variables.past_rain.pop(0)
        global_variables.past_temp.append(weather_data['current']['temp_c'])
        global_variables.past_temp.pop(0)
        global_variables.past_cloud.append(weather_data['current']['cloud'])
        global_variables.past_cloud.pop(0)
        global_variables.past_uv.append(weather_data['current']['uv'])
        global_variables.past_uv.pop(0)
        global_variables.past_humidity.append(weather_data['current']['humidity'])
        global_variables.past_humidity.pop(0)
        global_variables.past_wind_speed.append(weather_data['current']['humidity'])
        global_variables.past_wind_speed.pop(0)
        global_variables.past_pressure.append(weather_data['current']['humidity'])
        global_variables.past_pressure.pop(0)


# Initialize the authentication process for the connection to FarmBot API
def initialize(data):
    # Inputs for the FarmBot webapp:
    email = data['email']
    password = data['password']

    # Get your FarmBot Web App token.
    headers = {'content-type': 'application/json'}
    user = {'user': {'email': email, 'password': password}}
    response = requests.post('https://my.farmbot.io/api/tokens',
                             headers=headers, json=user)
    my_token = response.json()['token']['encoded']
    my_device_id = response.json()['token']['unencoded']['bot']
    mqtt_host = response.json()['token']['unencoded']['mqtt']

    # Connect to the broker...
    client = mqtt.Client()
    # ...using credentials from `token_generation_example.py`
    client.username_pw_set(my_device_id, my_token)

    client.connect("clever-octopus.rmq.cloudamqp.com", 1883, 60)

    return client, my_device_id, my_token


# Check the weather forecast
def weather_check(weather_data):
    # Get the current time and round it
    t = time.localtime()
    time_hour = int(time.strftime("%H", t))
    time_minute = int(time.strftime("%M", t))
    if time_minute > 30:
        if time_hour != 23:
            time_hour = time_hour+1
        else:
            time_hour = 0

    # Define arrays for weather forecast
    precipitation = np.zeros(4)
    will_rain = np.zeros(4)
    chance_rain = np.zeros(4)
    temperature = np.zeros(4)
    cloud = np.zeros(4)
    humidity = np.zeros(4)

    # Check for the switch to next day and get the data for the next 4 hours
    if time_hour < 19:
        j = 0
        for i in range(time_hour+1, time_hour+5, 1):
            precipitation[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['precip_mm']
            will_rain[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['will_it_rain']
            temperature[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['temp_c']
            chance_rain[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['chance_of_rain']
            cloud[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['cloud']
            humidity[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['humidity']
            j = j+1
    else:
        t1 = (time_hour + 1) % 24
        t2 = (time_hour + 2) % 24
        t3 = (time_hour + 3) % 24
        t4 = (time_hour + 4) % 24
        t1234 = np.array([t1, t2, t3, t4])
        j = 0
        for i in t1234:
            if i < 24 and i > time_hour:
                precipitation[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['precip_mm']
                will_rain[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['will_it_rain']
                temperature[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['temp_c']
                chance_rain[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['chance_of_rain']
                cloud[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['cloud']
                humidity[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['humidity']
                j = j+1
            else:
                precipitation[j] = weather_data['forecast']['forecastday'][1]['hour'][i]['precip_mm']
                will_rain[j] = weather_data['forecast']['forecastday'][1]['hour'][i]['will_it_rain']
                temperature[j] = weather_data['forecast']['forecastday'][1]['hour'][i]['temp_c']
                chance_rain[j] = weather_data['forecast']['forecastday'][1]['hour'][i]['chance_of_rain']
                cloud[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['cloud']
                humidity[j] = weather_data['forecast']['forecastday'][0]['hour'][i]['humidity']
                j = j+1

    return precipitation, will_rain, chance_rain, temperature, cloud, humidity


def turn_on_water(client, my_device_id):
    celery_script_turn_on_water = {
      "kind": "write_pin",
      "args": {
        "pin_mode": 0,
        "pin_value": 1,
        "pin_number": {
          "kind": "named_pin",
          "args": {
            "pin_id": 39865,
            "pin_type": "Peripheral"
          }
        }
      },
      "comment": "Turn on water"
    }
    # Encode it as JSON...
    json_payload = json.dumps(celery_script_turn_on_water)
    client.publish("bot/" + my_device_id + "/from_clients", json_payload)


def turn_off_water(client, my_device_id):
    celery_script_turn_off_water = {
      "kind": "write_pin",
      "args": {
        "pin_mode": 0,
        "pin_value": 0,
        "pin_number": {
          "kind": "named_pin",
          "args": {
            "pin_id": 39865,
            "pin_type": "Peripheral"
          }
        }
      },
      "comment": "Turn off water"
    }
    # Encode it as JSON...
    json_payload = json.dumps(celery_script_turn_off_water)
    client.publish("bot/" + my_device_id + "/from_clients", json_payload)


def change_light_status(client, my_device_id):
    celery_script_rpc = {
        "kind": "rpc_request",
        "args": {
            "label": "cb78760b-d2f7-4dd1-b8ad-ce0626b3ba53"
        },
        "body": [{
            "kind": "toggle_pin",
            "args": {
                "pin_number": 7
            }
        }]
    }

    # Encode it as JSON...
    json_payload = json.dumps(celery_script_rpc)
    client.publish("bot/" + my_device_id + "/from_clients", json_payload)


def take_photo(client, my_device_id):
    celery_take_photo = {
        "kind":"rpc_request",
        "args":{"label":"1880bb37-a1ab-4c65-947c-3f91bf17d473","priority":600},
        "body":[{"kind":"take_photo","args":{}}]
    }

    # Encode it as JSON...
    json_payload = json.dumps(celery_take_photo)
    client.publish("bot/" + my_device_id + "/from_clients", json_payload)


def go_to(client, my_device_id, x,y,z):
    celery_script_go_to = {
        "kind": "rpc_request",
        "args": {
            "label": "MY_EXAMPLE_RPC_0x03ABC"  # Use UUIDs in realworld apps
        },
        "body": [{
            "kind": "move_absolute",
            "args": {
                "speed": 100,
                "offset": {
                    "kind": "coordinate",
                    "args": {
                        "z": 0,
                        "y": 0,
                        "x": 0
                    }
                },
                "location": {
                    "kind": "coordinate",
                    "args": {
                        "z": z,
                        "y": y,
                        "x": x
                    }
                }
            }
        }]
    }
    # Encode it as JSON...
    json_payload = json.dumps(celery_script_go_to)
    client.publish("bot/" + my_device_id + "/from_clients", json_payload)


def retrieve_photo(API_TOKEN, number):
    headers = {'Authorization': 'Bearer ' + API_TOKEN,
               'content-type': "application/json"}
    response = requests.get('https://my.farmbot.io/api/images', headers=headers)
    images = response.json()
    most_recent_image_url = images[number]['attachment_url']
    response = requests.get(most_recent_image_url)
    filename = "image" + str(number) + ".jpg"
    with open(filename, "wb") as f:
        f.write(response.content)


def mount_tool(client, my_device_id):
    celery_script_mount_tool = {
        "kind": "lua",
        "args": {
            "lua": "mount_tool(variable(\"Seeder\"))"
        }
    }

    json_payload = json.dumps(celery_script_mount_tool)
    client.publish("bot/" + my_device_id + "/from_clients", json_payload)


def get_name_plants(API_TOKEN): # Return the name of teh plants that are in the garden
    headers = {'Authorization': 'Bearer ' + API_TOKEN,
               'content-type': "application/json"}
    response = requests.get('https://my.farmbot.io/api/plant_templates', headers=headers)
    plants = response.json()
    return plants


# Detect the ripeness of each plant
def detect_ripeness(diameter, age, spread, maxtime):
    ripe = 0
    if(diameter < 0.1) & (age > maxtime):
        ripe = 2 #code for plant has not grown, weed and free up the space for new plant
    if diameter > spread:
        ripe = 1
    else:
        ripe = 0
    return ripe


# Control the position of the tarpaulin
def tarpaulin(x):
    if x == 1:
        x = x+1
    else:
        x = 0