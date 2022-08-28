#!/usr/bin/env python3
import io
import time
import picamera
from fractions import Fraction
from influxdb import InfluxDBClient
from influxdb import SeriesHelper
import shutil
import meter_reader
import datetime
from pathlib import Path

# InfluxDB connection settings
influx_host = '192.168.1.2'
influx_port = 8086
influx_dbname = 'vesi'
influx_username = ''
influx_password = ''

# Path to black and white image of one dial. This is rotated and xor'ed over
# each dial. The angle with least amount of white should be the angle of the
# dial.
mask_image = '/home/pi/water_meter/mask_small.png'

# Paths to write water meter images
water_image_raw = '/mnt/ramdisk/water_raw.jpg'
water_image_raw_previous = '/mnt/ramdisk/water_raw_previous.jpg'
water_image_raw_write = '/mnt/ramdisk/water_raw_write.jpg'

# Archive to store images for debugging purposes
archive_path = '/home/pi/water_meter/archive/'

# Camera settings
camera_resolution = (1280, 720)
camera_iso = 800
camera_initial_sleep_time = 2
camera_shutter_speed = 12000
camera_red_gain = Fraction(1.5)
camera_blue_gain = Fraction(2.0)

mask_dict = meter_reader.create_mask_dict(mask_image)
myclient = InfluxDBClient(host=influx_host, port=influx_port, database=influx_dbname, username=influx_username, password=influx_password)


class MySeriesHelper(SeriesHelper):
    """Instantiate SeriesHelper to write points to the backend."""

    class Meta:
        """Meta class stores time series helper configuration."""

        # The client should be an instance of InfluxDBClient.
        client = myclient

        # The series name must be a string. Add dependent fields/tags
        # in curly brackets.
        series_name = 'consumption'

        # Defines all the fields in this time series.
        fields = ['amount_dl']

        tags = []

        # Defines the number of data points to store prior to writing
        # on the wire.
        bulk_size = 1

        # autocommit must be set to True when using bulk_size
        autocommit = True


def get_last_amount():
    query_result = myclient.query("SELECT amount_dl from consumption ORDER by time DESC LIMIT 1")
    last_amount = next(query_result.get_points())['amount_dl']
    return last_amount


def archive_value(amount_dl, source_path):
    destination_path = archive_path + datetime.datetime.now().strftime(
        '%Y%m%d%H%M%S') + '_' + str(amount_dl) + ".jpg"

    print("Destination path: " + destination_path)
    shutil.copy(source_path, destination_path)
    return


def capture_images():
    last_amount = get_last_amount()
    amount_cubic_meters = int(last_amount / 10000) * 10000
    previous_amount_dl = last_amount - amount_cubic_meters
    Path(water_image_raw).touch()
    print("Last cubic meter cubic meters: {}, deciliters {}".format(amount_cubic_meters, previous_amount_dl))

    with picamera.PiCamera() as camera:
        setup_camera(camera)
        stream = io.BytesIO()
        time1 = time.time()
        for foo in camera.capture_continuous(stream, format='jpeg'):
            stream.truncate()
            stream.seek(0)
            with open(water_image_raw_write, "wb") as f:
                f.write(stream.getvalue())
            shutil.copy(water_image_raw, water_image_raw_previous)
            shutil.move(water_image_raw_write, water_image_raw)
            amount_dl = meter_reader.read_meter(water_image_raw)

            # Comment this to not to write measurements to archive for
            # debugging purposes
            # archive_value(amount_dl, water_image_raw)

            if previous_amount_dl > 9000 and amount_dl < 1000:
                amount_cubic_meters = amount_cubic_meters + 10000

            stored_result = amount_cubic_meters + amount_dl
            time2 = time.time()
            measure_time = time2 - time1
            print("Measuring took {}s, previous measurement: {}, new measurement: {}".format(measure_time, previous_amount_dl, amount_dl))
            print("Current water consumption is {}dl".format(stored_result))

            # Archive suspect values for debugging. If consumption between
            # measurements is negative or if consumption between measurements
            # is over 100dl, archive previous and current image
            if amount_dl - previous_amount_dl < 0 or amount_dl - previous_amount_dl > 100:
                archive_value(previous_amount_dl, water_image_raw_previous)
                archive_value(amount_dl, water_image_raw)

            MySeriesHelper(amount_dl=stored_result)

            previous_amount_dl = amount_dl
            time.sleep(10 - measure_time)
            time1 = time.time()


def setup_camera(camera):
    camera.resolution = camera_resolution
    camera.iso = camera_iso
    time.sleep(camera_initial_sleep_time)
    camera.shutter_speed = camera_shutter_speed
    camera.exposure_mode = 'off'
    camera.awb_mode = 'off'
    gains = (camera_red_gain, camera_blue_gain)
    camera.awb_gains = gains


if __name__ == "__main__":
    capture_images()
