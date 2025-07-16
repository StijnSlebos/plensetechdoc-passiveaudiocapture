""""
This code manages the calibration of the ultrasound sensors.
It uses the capture manager to capture audio data for 5 seconds from both sensors.
After that it plots both datasets.

The user will first hit the first sensor once and then the second sensor once.
Based on the plot the user will assign the correct sensor to the correct batsound_id in the sensor_allocation.json file.

Finally it loads the force sensor interface allowinge the user to clamp the sensor at the right force.
This force is then saved to the sensor_allocation.json file.
"""

import logging

class CalibrationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Building calibration manager...")

