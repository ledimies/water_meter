#!/usr/bin/env python3
import cv2
import meter_reader

# The raw source image of the water meter
water_image_raw = './water_raw.jpg'
mask_image = './mask_small.png'

def animate(needle):
  for x in range(0, 359):
    xor = cv2.bitwise_xor(mask_dict[x], needle)
    cv2.imshow('xor animation', xor)
    cv2.waitKey(5)


def show_angle(needle, angle, needle_name):
  xor = cv2.bitwise_xor(mask_dict[angle], needle)
  cv2.imshow(needle_name, xor)

# Initialize angle to mask -cache
mask_dict = meter_reader.create_mask_dict(mask_image)

img = cv2.imread(water_image_raw)
mask = meter_reader.convert_meter_image_to_mask(img)

# TODO: Move magic numbers to definitions
# Crop each dial from mask image
needle_1 = mask[493:493+150, 371:371+150]
needle_10 = mask[566:566+150, 609:609+150]
needle_100 = mask[494:494+150, 785:785+150]
needle_1000 = mask[335:335+150, 888:888+150]

needle_1_angle_offset = -8
needle_10_angle_offset = -8
needle_100_angle_offset = -8
needle_1000_angle_offset = -8

needle_rectangles_with_offsets = [(needle_1, needle_1_angle_offset),
                                  (needle_10, needle_10_angle_offset),
                                  (needle_100, needle_100_angle_offset),
                                  (needle_1000, needle_1000_angle_offset)]
needle_angles = meter_reader.read_needles(needle_rectangles_with_offsets)
needle_values = [value / 36 for value in needle_angles]
value = meter_reader.determine_value(needle_values)

print("Needle angles:", needle_angles)
print("Raw values:")
print("Value 0.1:", needle_values[3])
print("Value 0.01:", needle_values[2])
print("Value 0.001:", needle_values[1])
print("Value 0.0001:", needle_values[0])
print("Final value:", value)

# Visualize results
animate(needle_1)
show_angle(needle_1000, needle_angles[3], "0.1")
show_angle(needle_100, needle_angles[2], "0.01")
show_angle(needle_10, needle_angles[1], "0.001")
show_angle(needle_1, needle_angles[0], "0.0001")

cv2.imshow('raw image', img)
cv2.imshow('mask image', mask)
cv2.waitKey(0)
cv2.destroyAllWindows()
