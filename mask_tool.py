#!/usr/bin/env python3
import numpy as np
import cv2
import argparse

# This script can be used to find the right HSV color bounds to
# make a suitable mask of the water meter dials. See link
# https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html
# for more information about HSV color space and how to use it to
# track specific color objects.
#
# In this case the water meter has red dials and there is very little
# red in the image other than the dials.

# Read file
parser = argparse.ArgumentParser(description='Reads a water meter image and generates mask image')
parser.add_argument('image_path', help='Path to image')
args = parser.parse_args()
water_image_raw = args.image_path

# Written files
water_image_black_and_white = './water_bw.jpg'
water_image_just_dials = './water_dials.jpg'

# Read sourca image
img = cv2.imread(water_image_raw, cv2.IMREAD_COLOR)

# Convert to HSV color space
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Create a mask
lower_red = np.array([1,140,0])
upper_red = np.array([10,180,255])
mask = cv2.inRange(hsv, lower_red, upper_red)

dials = img.copy()
dials = cv2.bitwise_and(dials, dials, mask=mask)

# Show images
cv2.imshow('Mask', mask)
cv2.imshow('And', dials)
cv2.imshow('Raw', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
