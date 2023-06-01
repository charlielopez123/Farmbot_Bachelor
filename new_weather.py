"""
Main program.
This program contains the algorithm to automate the FarmBot response to the weather and command the actions.
The program reacts to the weather forecast by acting on the watering system and the tarpaulin.
It manages to provide enough water for each plant for the whole lifetime of the plant and prevent it to burn at the sun.
The program also tracks the plant growth with a diameter based growth approximation

The functions are called base on the current time and the schedule.

June 2023
Version 1
"""

import requests
import json
import schedule
import time
import numpy as np
import math
import Openfarm_API

import functions
import open_plant_json

from photo_to_diameter_cm import get_diameter_cm

import global_variables

# Define the debit of the water
DEBIT = 0.5

# Open the json file where the password is stored
with open("password.json", "r") as jsonfile:
    data = json.load(jsonfile)

# Initialize the communication with the FarmBot API
output_init = functions.initialize(data)

# Authentication data for the FarmBot API
client = output_init[0]
my_device_id = output_init[1]
token = output_init[2]

"""
Main function, where all the automation process is done.
Keep track of the number of plants, their age and their recommended soil moisture level.
Predict the necessity of closing the tarpaulin based on the radiation, the rain forecast and the current soil moisture.

The list of the plants in the garden can be updated through the FarmBot Web App.
"""


def main():

    add_age = np.ones(len(global_variables.age))  # Initialize

    global_variables.age = global_variables.age + add_age

    # Open the json file where the password is stored
    with open("password.json", "r") as datafile:
        data = json.load(datafile)

    # Setting up the API call
    res = requests.get(data['url1'])
    weather_data = res.json()

    # Get the weather infos for the next 4 hours
    weather = functions.weather_check(weather_data)

    precipitation = weather[0]
    will_rain = weather[1]

    # Get the list of plants
    plants = functions.get_name_plants(token)

    # Create the plant names table to the current plants in the garden
    global_variables.plant_names = []
    for i in range(len(plants)):
        global_variables.plant_names.append(plants[i]['name'])

    # Adapt the different vectors in case of a plant removal in the Web App
    if len(global_variables.plant_names) < len(global_variables.old_plant_names):
        diff = np.setdiff1d(global_variables.old_plant_names, global_variables.plant_names)
        for i in range(len(diff)):
            global_variables.plant_pos_x.pop(i)
            global_variables.plant_pos_y.pop(i)
            global_variables.age.pop(i)
            global_variables.moist_recommendation.pop(i)
            global_variables.plant_diameter.pop(i)

    # Check if the list of plants as changed
    if global_variables.old_plant_names != global_variables.plant_names:
        global_variables.old_plant_names = global_variables.plant_names

        # Adapth the changes for the position of the plants and the age
        for i in range(len(global_variables.plant_names)):
            global_variables.plant_pos_x.append(plants[i]['x'])
            global_variables.plant_pos_y.append(plants[i]['y'])
            global_variables.age = np.append(global_variables.age, [0])

            global_variables.plant_diameter.append(0)

            # Get the moist recommendation for each plant
            moist = open_plant_json.get_moist(global_variables.plant_names[i])
            global_variables.moist_recommendation.append(moist)

            if moist == -1:
                print("The OpenPlantAPI cannot find the scientific name for the plant: ", global_variables.plant_names[i])
                print("Try changing the plant in the FarmBot Web App into a more common named one and retry")
                print("The soil moisture is set to 50% and the acceptable temperature range to [5-30] °C by default")
                print("")

    # Check if the tarpaulin needs to be closed if there is too much radiation and the soil is too dry
    if (global_variables.ghi_true > 700) & (global_variables.moisture < 60):
        global_variables.tarpaulin_state = 1
    else:
        global_variables.tarpaulin_state = 0

    # Check if the tarpaulin needs to be closed if there is too much rain and the soil is too wet
    if np.sum(precipitation) > 2 and global_variables.moisture > 80:
        global_variables.tarpaulin_state = 1
    else:
        global_variables.tarpaulin_state = 0

    # Reset the amount of water distributed (protection if bad timing with the moisture computation)
    global_variables.water_spilled = 0

    # Check if it is necessary to water the plants based on the soil moisture, the rain forecast and the radiation
    for i in range(len(global_variables.plant_names)):

        # Check in which part of life the plant is (62 * 4 hours = 10.5 days) and set the watering time accordingly
        if global_variables.age[i] < 62:
            time_sleep = 20
        elif (global_variables.age[i] > 62) and (global_variables.age[i] < 124):
            time_sleep = 10
        else:
            time_sleep = 5

        # Check name error
        if global_variables.moist_recommendation[i] == -1:
            if (global_variables.moisture < 50) and (np.sum(will_rain) == 0) and (global_variables.ghi_true < 1000):
                functions.go_to(client, my_device_id, global_variables.plant_pos_x[i], global_variables.plant_pos_y[i], 0)
                time.sleep(120)  # delay for the farmbot to go to the asked position
                functions.turn_on_water(client, my_device_id)
                time.sleep(time_sleep)
                functions.turn_off_water(client, my_device_id)

                # Compute the amount of water distributed
                global_variables.water_spilled = global_variables.water_spilled + time_sleep * DEBIT

        # The plants should not be watered if the radiation is too high
        if (global_variables.moisture < global_variables.moist_recommendation[i]) and (np.sum(will_rain) == 0) and (global_variables.ghi_true < 1000):
            functions.go_to(client, my_device_id, global_variables.plant_pos_x[i], global_variables.plant_pos_y[i], 0)
            time.sleep(120)  # delay for the farmbot to go to the asked position
            functions.turn_on_water(client, my_device_id)
            time.sleep(time_sleep)
            functions.turn_off_water(client, my_device_id)
            global_variables.water_spilled = global_variables.water_spilled + time_sleep * DEBIT

    # Set the tarpaulin state at the end of each iteration to avoid useless movement
    functions.tarpaulin(global_variables.tarpaulin_state)


"""
Functions to take a photo of each plant and compute the age based on the current diameter and the expected diameter.
It takes photo at night to prevent bad light on the camera since the quality is not that good.
"""


def photo_plants():

    # Closes the tarpaulin if it rains
    if global_variables.actual_precipitation > 0:
        if global_variables.tarpaulin_state == 0:
            functions.tarpaulin(1)

    # For each plant, go to the plant location, take the photo, upload it the the computer, process the diameter and age
    for i in range(len(global_variables.plant_names)):
        functions.go_to(client, my_device_id, global_variables.plant_pos_x[i], global_variables.plant_pos_y[i], 0)
        time.sleep(120)
        functions.change_light_status(client, my_device_id)
        time.sleep(5)
        functions.take_photo(client, my_device_id)
        time.sleep(5)
        functions.change_light_status(client, my_device_id)
        time.sleep(5)
        functions.retrieve_photo(token, 0)
        global_variables.plant_diameter[i] = get_diameter_cm("image0.jpg")
        max_spread = Openfarm_API.find_spread(global_variables.plant_names[i])  # max spread from Openfarm database
        ripe = functions.detect_ripeness(global_variables.plant_diameter[i], global_variables.age, max_spread, maxtime=180 * 4)  # maxtime is set at 30 days = 180*4 hours
        if ripe == 1:
            print("Plant", global_variables.plant_names[i], "is ready for harvest")
        if ripe == 2:
            print("Plant", global_variables.plant_names[i], "has not grown to full size, go check at position x = ", global_variables.plant_pos_x[i], ", y = ", global_variables.plant_pos_y[i])
        print(global_variables.plant_diameter[i])

    # Return to home
    functions.go_to(client, my_device_id, 0, 0, 0)
    if global_variables.tarpaulin_state == 0:
        functions.tarpaulin(0)


"""
Functions to compute the moisture of the soil since the moisture sensor does not work properly.
It uses radiation, rain level, humidity, pressure, temperature and wind speed
"""


def compute_moist():
    t = time.localtime()

    # Define the ghi = radiation value
    if t.tm_hour > 21 or t.tm_hour < 5:
        global_variables.ghi = 0

    else:
        res = requests.get(data["url4"])
        global_variables.ghi = res.json()

        global_variables.ghi = global_variables.ghi["estimated_actuals"][0]["ghi"]
        global_variables.ghi_true = global_variables.ghi

    if global_variables.tarpaulin_state == 1:
        global_variables.ghi_true = global_variables.ghi
        global_variables.ghi = 0.1 * global_variables.ghi

    rn = global_variables.ghi

    # Temperature value
    temp = global_variables.past_temp[-8:]  # last 8 items in the array, updated every 15 minutes --> 2 hours
    t = np.sum(temp)/8

    # Relative humidity
    hum = global_variables.past_humidity[-8:]  # last 8 items in the array, updated every 15 minutes --> 2 hours
    rh = np.sum(hum)/8

    # Wind speed
    ws = global_variables.past_wind_speed[-8:]  # last 8 items in the array, updated every 15 minutes --> 2 hours
    u = np.sum(ws)/8

    # Pressure
    pressure = global_variables.past_pressure[-8:]
    p = np.sum(pressure)/8

    # Rain
    rain = global_variables.past_rain[-8:]
    rain = np.sum(rain)/8

    # Penman-Monteith Equation
    delta = 4098 * (0.6108 * math.exp((17.27 * t) / (t + 273))) / (t + 273.3)
    g = 0.1 * rn
    gamma = 0.665 * p  # P in Pascals
    u2 = 0.817 * u
    es = 0.6108 * math.exp((17.27 * t) / (t + 237.3))
    ea = rh / 100 * es  # RH Relative humidity in %
    e_t0 = (0.408 * delta * (rn - g)*0.01 + gamma * 9.375 / (t + 273) * u2 * (es - ea)) / (delta + gamma * (1 + 0.34 * u2))

    # Water volume in the field
    global_variables.water_volume = global_variables.water_volume + 18*(rain - e_t0) + global_variables.water_spilled

    # Reset the amount of water distributed by the system to prevent counting ot twice
    # since moisture computed every 2 hours and main run every 4 hours
    global_variables.water_spilled = 0

    # Field moisture
    global_variables.moisture = global_variables.water_volume / global_variables.max_volume_field

    if global_variables.moisture > 100:
        global_variables.moisture = 100
    elif global_variables.moisture < 0:
        global_variables.moisture = 0

# # Avoid take in account computation time
# schedule.every().day.at("00:00").do(main)
# schedule.every().day.at("04:00").do(main)
# schedule.every().day.at("08:00").do(main)
# schedule.every().day.at("12:00").do(main)
# schedule.every().day.at("16:00").do(main)
# schedule.every().day.at("20:00").do(main)

# schedule.every().day.at("02:00").do(photo_plants)

# schedule.every(2).hours.do(compute_moist)

# while(1):
#     schedule.run_pending()
#     time.sleep(1)
