"""
File with the definition of variables used across several files

June 2023
"""

old_plant_names = []
plant_names = []  # get the name of the plants

moist_recommendation = []

plant_pos_x = []  # get the x position of the plants
plant_pos_y = []  # get the y position of the plants
plant_diameter = [] # radius of the plant, see the photo_to_diameter file

age = []

past_rain = [-100] * 672  # initialize the arrays to track the past weather
past_temp = [-100] * 672
past_cloud = [-100] * 672
past_uv = [-100] * 672
past_humidity = [-100] * 672
past_wind_speed = [-100] * 672
past_pressure = [-100] * 672

max_volume_field = 540  # [L] maximum water capacity of the field given the field capacity of 0.3 and the field volume
water_volume = 0
moisture = 0  # soil moisture
temp_0 = 0 # Soil temperature at 0 cm depth
temp_10 = 0 # Soil temperature at 10 cm depth

water_spilled = 0 # Water spilled by the integrated watering system

ghi = 0 # Radiation value

date_last_update = ""  # initialize the last moment when the weather was updated

actual_precipitation = 0

tarpaulin_state = 0

ghi_true = 0