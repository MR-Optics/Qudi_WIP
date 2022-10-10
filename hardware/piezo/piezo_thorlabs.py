# -*- coding: utf-8 -*-
"""
This file contains the Qudi module for the KCube Piezo Controller - KPZ101. - Not on GitHub right now.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

#TODO: Hardware should only connect one device.

#TODO: Transfer computations to the logic.

#

import numpy as np
import time
import os
import sys
import clr  # Requires pythonnet: pip install pythonnet

from core.module import Base
from core.connector import Connector
from core.configoption import ConfigOption
from interface.controller_interface import ControllerInterface

# Accessing MotionControl:
if 1:
    piezo_file = "C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.KCube.PiezoCLI.dll"
    piezo_dm_file = "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll"
    piezo_gm_file = "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll"
    piezo_gp_file = "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericPiezoCLI.dll"

    clr.AddReference(piezo_file)
    clr.AddReference(piezo_dm_file)
    clr.AddReference(piezo_gp_file)
    clr.AddReference(piezo_gm_file)

    from Thorlabs.MotionControl.DeviceManagerCLI import *
    from Thorlabs.MotionControl.GenericMotorCLI import *
    from Thorlabs.MotionControl.KCube.PiezoCLI import *
    from Thorlabs.MotionControl.GenericPiezoCLI import *

    from System import Decimal  # necessary for real world units

class KPZ101(Base, ControllerInterface):
    """ KCube Piezo Controller - KPZ101.

    Example: config for copy-paste:

    piezo:
        module.Class: 'piezo.piezo_thorlabs.KPZ101'
    """

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        pass

    # Initialization:
    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """

        try:
            # Build device list:
            DeviceManagerCLI.BuildDeviceList()
        except:
            self.log.error("Device list was not built.")
            return -1

        try:
            # Retrieve serial numbers:
            self._serial_nos = DeviceManagerCLI.GetDeviceList()
        except:
            self.log.error("Serial numbers were not retrieved.")

        #  Check if no devices are connected:
        if self._serial_nos == []:
            self.log.error("No MotionControl Devices were found. "
                           "Make sure the devices are connected. ")
            return -1

        """ Note: All serial numbers of Thorlabs' devices are related to the type of 
        equipment. Hence, we can check for specific devices by comparing the 
        first two digits. Below a short list can be found
        
        KCube:
            Piezo Controller: 29xxxxxx
            Strain Gauge Controller: 59xxxxxx
        """

        # Retrieve piezo controller serial numbers:
        self._pz_id = "29"
        self._pz_serial_nos = [sn for sn in self._serial_nos if self._pz_id in sn[0:2]]

        # Check if no piezo controllers were found:
        if len(self._pz_serial_nos) == 0:
            self.log.error("No Piezo Controller Devices were found. ")
            return -1

        # Sort list of serial numbers:
        self._pz_serial_nos.sort()

        print(self._pz_serial_nos)

        # Create list of piezos:
        self._piezos = []
        for pz in self._pz_serial_nos:
            self._piezos.append(self.setup_piezo(pz))

        return 0

    def setup_piezo(self, serial_no):

        # Create device:
        device = KCubePiezo.CreateKCubePiezo(serial_no)

        # Connect device:
        device.Connect(serial_no)

        # Check for initialization and wait if not done:
        if not device.IsSettingsInitialized():
            self.log.info("Initializing Piezo S/N: " + str(serial_no))
            device.WaitForSettingsInitialized(2000)

            if device.IsSettingsInitialized():
                self.log.info("Initialization completed")

        # Begin polling:
        device.StartPolling(250)

        # Configure device:
        device.GetPiezoConfiguration(serial_no)
        time.sleep(0.25)

        # Zero device:
        device.SetZero()

        # Enable device:
        device.EnableDevice()

        return device

    # De-initialization:
    def on_deactivate(self):
        """ Reverse the activation process.
        """

        for pz in self._piezos:
            pz.DisableDevice()
            pz.Disconnect()

        return self.reset_hardware()

    def reset_hardware(self):
        """
        Reset the hardware, so the connection is lost and other programs can
        access it.

        @return int: error code: (0:OK, -1:error)
        """
        self.log.warning("Piezo KPZ101 will be reset.")
        return 0

    # Operations:
    def move(self, direction):
        # print("Piezo moved " + direction + ".")

        self._piezo_x_dir = self._piezos[2]
        self._piezo_z_dir = self._piezos[1]
        self._piezo_y_dir = self._piezos[0]

        self._x_pz = Decimal.ToDouble(self._piezo_x_dir.GetOutputVoltage())
        self._y_pz = Decimal.ToDouble(self._piezo_y_dir.GetOutputVoltage())
        self._step_size = 0.1

        if direction == "forward":
            self._y_pz -= self._step_size
            self._piezo_y_dir.SetOutputVoltage(Decimal(self._y_pz))

        if direction == "backward":
            self._y_pz += self._step_size
            self._piezo_y_dir.SetOutputVoltage(Decimal(self._y_pz))

        if direction == "left":
            self._x_pz += self._step_size
            self._piezo_x_dir.SetOutputVoltage(Decimal(self._x_pz))

        if direction == "right":
            self._x_pz -= self._step_size
            self._piezo_x_dir.SetOutputVoltage(Decimal(self._x_pz))

        print("x: {:.2f} \t y: {:.2f}".format(self._x_pz, self._y_pz))

        return 0

    def close(self):
        """ Closes the hardware and cleans up afterwards.

        @return int: error code(0:OK, -1:error)
        """
        self.log.debug("KPZ101>close")
        return 0
