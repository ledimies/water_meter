import numpy as np
import cv2
from math import floor

mask_dict = {}

# The mask values below were found with trial&error using helper script
# mask_tool.py
# Lighter reds
lower_red_mask_1 = np.array([1,140,0])
upper_red_mask_1 = np.array([6,180,255])
# Darker reds
lower_red_mask_2 = np.array([6,125,50])
upper_red_mask_2 = np.array([11,140,200])


def rotate_image(image, angle):
  image_center = tuple(np.array(image.shape[1::-1]) / 2)
  rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
  result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
  return result


# Create a cache dictionary from rotation angle to mask dial
def create_mask_dict(mask_image):
  global mask_dict
  mask = cv2.imread(mask_image)
  gray_mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
  (thresh, bw_mask) = cv2.threshold(gray_mask, 127, 255, cv2.THRESH_BINARY)
  for x in range(0, 359):
    rot_mask = rotate_image(bw_mask, -x)
    mask_dict[x] = rot_mask
  return mask_dict


# XOR each angle of the mask dial over the black&white image of each dial.
# The angle of the dial is the iteration where the XOR result has the least
# amount of white
def read_needle(needle, angle_offset):
  angle = -1
  min = 150*150
  for x in range(0, 359):
    xorred = cv2.bitwise_xor(mask_dict[x], needle)
    sum = np.sum(xorred == 255)
    if sum < min:
      min = sum
      angle = x
  angle = angle - angle_offset
  if angle >= 360:
    angle = angle - 360
  elif angle < 0:
    angle = angle + 360
  return angle


def decrement(intvalue):
  if intvalue == 0:
    return 9
  return intvalue - 1


def increment(intvalue):
  if intvalue == 9:
    return 0
  return intvalue + 1


# Determines the value of water consumption in decilitres. Tries to determine
# if a dial value near the threshold of 9..0 is actually 9 or zero.
def determine_value(values):
  value = floor(values[0])
  less_significant_int = value
  multiplier = 10
  for more_significant in values[1:]:
    more_significant_int = floor(more_significant)
    more_significant_decimal = more_significant - more_significant_int
    if more_significant_decimal > 0.8 and less_significant_int < 5:
      more_significant_int = increment(more_significant_int)
    if more_significant_decimal < 0.2 and less_significant_int > 5:
      more_significant_int = decrement(more_significant_int)
    value = value + multiplier * more_significant_int
    less_significant_int = more_significant_int
    multiplier = multiplier * 10
  return value


def convert_meter_image_to_mask(image):
  hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

  # Brighter reds
  mask1 = cv2.inRange(hsv, lower_red_mask_1, upper_red_mask_1)

  # Darker reds
  mask2 = cv2.inRange(hsv, lower_red_mask_2, upper_red_mask_2)

  return mask1+mask2


def read_needles(needles):
  needle_angles = []
  for needle in needles:
    needle_angles.append(read_needle(needle[0], needle[1]))
  return needle_angles


def read_meter(water_image_raw):
  img = cv2.imread(water_image_raw)
  mask = convert_meter_image_to_mask(img)

  # TODO: Move magic numbers to definitions
  needle_1 = mask[493:493 + 150, 371:371 + 150]
  needle_10 = mask[566:566 + 150, 609:609 + 150]
  needle_100 = mask[494:494 + 150, 785:785 + 150]
  needle_1000 = mask[335:335 + 150, 888:888 + 150]

  needle_1_angle_offset = -8
  needle_10_angle_offset = -8
  needle_100_angle_offset = -8
  needle_1000_angle_offset = -8

  needle_rectangles_with_offsets = [(needle_1, needle_1_angle_offset),
                                    (needle_10, needle_10_angle_offset),
                                    (needle_100, needle_100_angle_offset),
                                    (needle_1000, needle_1000_angle_offset)]

  needle_angles = read_needles(needle_rectangles_with_offsets)
  print("Needles:", needle_angles)
  needle_values = [value / 36 for value in needle_angles]
  value = determine_value(needle_values)

  print("Raw values:")
  print("Value 0.1:", needle_values[3])
  print("Value 0.01:", needle_values[2])
  print("Value 0.001:", needle_values[1])
  print("Value 0.0001:", needle_values[0])
  print("Final value:", value)

  return value
