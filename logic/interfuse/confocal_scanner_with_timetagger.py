# -*- coding: utf-8 -*-
"""
Interfuse to do confocal scans with spectrometer data rather than APD count rates.

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

import time
import numpy as np
from time import sleep

from core.module import Base
from core.configoption import ConfigOption
from core.util.mutex import Mutex
from core.connector import Connector
from interface.confocal_scanner_interface import ConfocalScannerInterface

#TODO Not tested in practice!


class ScannerInterfuse(Base, ConfocalScannerInterface):

    """This is the Interface class to define the controls for the simple
    microwave hardware.
    """

    # connectors
    confocalscanner1 = Connector(interface='ConfocalScannerInterface')
    slowcounter = Connector(interface='FastCounterInterface')

    # config options
    _clock_frequency = ConfigOption('clock_frequency', 100, missing='warn')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.threadlock = Mutex()


    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """

        self._scanner_hw = self.confocalscanner1()
        self._slowcounter_hw = self.slowcounter()


    def on_deactivate(self):
        self.reset_hardware()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs can access it.

        @return int: error code (0:OK, -1:error)
        """
        self.log.warning('Scanning Device will be reset.')
        return 0

    def get_position_range(self):
        """ Returns the physical range of the scanner.
        This is a direct pass-through to the scanner HW.

        @return float [4][2]: array of 4 ranges with an array containing lower and upper limit
        """
        return self._scanner_hw.get_position_range()

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.
        This is a direct pass-through to the scanner HW

        @param float [4][2] myrange: array of 4 ranges with an array containing lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [[0,1],[0,1],[0,1],[0,1]]

        self._scanner_hw.set_position_range(myrange=myrange)

        return 0

    def set_voltage_range(self, myrange=None):
        """ Sets the voltage range of the NI Card.
        This is a direct pass-through to the scanner HW

        @param float [2] myrange: array containing lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [-10.,10.]

        self._scanner_hw.set_voltage_range(myrange=myrange)
        return 0

    def set_up_scanner_clock(self, clock_frequency = None, clock_channel = None):
        """ Configures the hardware clock of the NiDAQ card to give the timing.
        This is a direct pass-through to the scanner HW

        @param float clock_frequency: if defined, this sets the frequency of the clock
        @param string clock_channel: if defined, this is the physical channel of the clock

        @return int: error code (0:OK, -1:error)
        """

        self._count_frequency = clock_frequency

        return self._scanner_hw.set_up_scanner_clock(clock_frequency=clock_frequency, clock_channel=clock_channel)


    def set_up_scanner(self, counter_channels = None, sources = None, clock_channel = None, scanner_ao_channels = None):
        """ Configures the actual scanner with a given clock.

        @param string counter_channel: if defined, this is the physical channel of the counter
        @param string photon_source: if defined, this is the physical channel where the photons are to count from
        @param string clock_channel: if defined, this specifies the clock for the counter
        @param string scanner_ao_channels: if defined, this specifies the analoque output channels

        @return int: error code (0:OK, -1:error)
        """

        if self._scanner_hw._pixel_clock_channel is None:
            self.log.error('Please specify the NI\'s pixel_clock_channel and connect it to TimeTagger')

        return self._scanner_hw.set_up_scanner(counter_channels=counter_channels,
                                               sources=sources,
                                               clock_channel=clock_channel,
                                               scanner_ao_channels=None)

    def get_scanner_axes(self):
        """ Pass through scanner axes. """
        return self._scanner_hw.get_scanner_axes()

    def scanner_set_position(self, x = None, y = None, z = None, a = None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).
        This is a direct pass-through to the scanner HW

        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """

        self._scanner_hw.scanner_set_position(x=x, y=y, z=z, a=a)
        return 0

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[]: current position in (x, y, z, a).
        """

        return self._scanner_hw.get_scanner_position()

    def scan_line(self, line_path=None, pixel_clock=False):
        """ Scans a line and returns the counts on that line.

        @param float[][4] line_path: array of 4-part tuples defining the voltage points
        @param bool pixel_clock: whether we need to output a pixel clock for this line

        @return float[]: the photon counts per second
        """
        with self.threadlock:
            self._line_length = np.shape(line_path)[1]
            self._slowcounter_hw.configure_count_between_markers(self._line_length)
            self._slowcounter_hw.start_measure_sc()

            data = self._scanner_hw.scan_line(line_path=line_path, pixel_clock=pixel_clock)

            count_data = np.zeros((self._line_length,1))

            if len(data) != self._line_length:
                self.log.error('Line length is not correctly configured in interfuse')

            if pixel_clock is True:
                while not self._slowcounter_hw.is_array_filled():
                    sleep(0.0001)

            self._slowcounter_hw.stop_measure_sc()
            bin_count_data, info = self._slowcounter_hw.get_data_trace_sc()

            count_data[:,0] = bin_count_data * self._count_frequency

        return count_data

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        self._scanner_hw.close_scanner()

        return 0

    def close_scanner_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        self._scanner_hw.close_scanner_clock()
        return 0

    def get_scanner_count_channels(self):

        return self._scanner_hw.get_scanner_count_channels()
