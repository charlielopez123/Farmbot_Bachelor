# Everything_photo.py receives as input image_string of the photo taken, and returns the diameter in cm of the smallest
# circle enclosing the object.
# The background of the image is removed from the photo by posting the photo to the remove.bg API, from which we can
# then retrieve the output image by writing it onto an output file
# Once the object is now isolated from the background, it is much easier to determine the contour around it. We start
# by converting the image in gray to allow for a thresholding of the image and apply a mask onto the object. We apply
# morphological operations to remove the noise. Once the largest contour is found, the smallest enclosing circle is
# determined and the value of its diameter in number of pixels is kept. Now that value just needs to be converted into
# centimeters with a simple conversion using a reference image with a known width

import requests
import json
import cv2

pixelsPerMetric = 16.93

def get_diameter_cm(image_string):
    remove_bg(image_string) # creates the output file called 'output_image.png' with removed background
    diameter = circle_lettuce('output_image.png')
    diameter_cm = pixel_to_cm(diameter)
    return diameter_cm

def remove_bg(image_string): # isolate the object of interest and remove the background
    # Open the JSON file for reading
    with open('API_Key_remove_bg.json', 'r') as f:
        # Load the api_key from the JSON data from the file
        api_key = json.load(f)['api_key']

    # Define the remove.bg API endpoint
    api_endpoint = "https://api.remove.bg/v1.0/removebg"

    # Define the input and output file paths
    input_file_path = image_string
    output_file_path = 'output_image.png'

    # Define the API request headers and parameters
    headers = {'X-Api-Key': api_key}
    parameters = {'size': 'auto'}

    # Open the input file and send a POST request to the API
    with open(input_file_path, 'rb') as f:
        response = requests.post(api_endpoint, headers=headers, params=parameters, files={'image_file': f})
        print(response)

    # Save the output image to the specified file path
    with open(output_file_path, 'wb') as f:
        f.write(response.content)

def circle_lettuce(output_image_string): # returns the diameter in pixels, of the enclosing circle of the lettuce

    # Load the image
    img = cv2.imread(output_image_string)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to create a binary image
    ret, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

    # Apply morphological operations to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=3)

    # Find contours in the binary image and keep the largest one
    contours, hierarchy = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    largest_contour = max(contours, key=cv2.contourArea)

    # Determine enclosing radius
    _, radius = cv2.minEnclosingCircle(largest_contour)
    radius = int(radius)
    diameter = radius * 2

    return diameter

def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

def pixel_to_cm(diameter):
    # compute the size of the object
    diameter_cm = diameter / pixelsPerMetric
    return diameter_cm