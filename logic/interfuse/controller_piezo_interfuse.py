# -*- coding: utf-8 -*-

"""
This file contains the Qudi Interfuse between Controller Logic and Piezo Hardware -
- Not on GitHub right now.

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

import copy

from core.connector import Connector
from logic.generic_logic import GenericLogic
from interface.controller_interface import ControllerInterface


class ControllerPiezoInterfuse(GenericLogic, ControllerInterface):
    """ This interfuse connects the Controller interface with the Piezo hardware.

    Example: config for copy-paste:
    controller_piezo_interfuse:
        module.Class: 'interfuse.controller_piezo_interfuse.ControllerPiezoInterfuse'
        connect:
            piezostage1: 'piezo'
    """

    piezostage1 = Connector(interface='ControllerInterface')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Initialization:
    def on_activate(self):
        """
        Initialisation performed during activation of the module.
        """
        self._piezo_device = self.piezostage1()

    # De-initialization:
    def on_deactivate(self):
        """ Resets the hardware, so the connection is lost and the other programs can access it.

        @return int: error code (0:OK, -1:error)
        """
        return self._piezo_device.reset_hardware()

    def close(self):
        """ Closes the hardware and cleans up afterwards.

        @return  int: error code(0:OK, -1:error)
        """
        return self._piezo_device.close()

    # Operation:
    def move(self, direction):
        """
        Moves the hardware in direction: dir.

        @return int: error code (0:OK, -1:error)
        """
        return self._piezo_device.move(direction)
