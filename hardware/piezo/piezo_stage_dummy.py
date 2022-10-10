# -*- coding: utf-8 -*-
"""
This file contains the Qudi dummy module for the piezo stage. - Not on GitHub right now.

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

import numpy as np
import time

from core.module import Base
from core.connector import Connector
from core.configoption import ConfigOption
from interface.controller_interface import ControllerInterface


class PiezoStageDummy(Base, ControllerInterface):
    """ Dummy piezo stage. Prints the moved direction in console.

    Example: config for copy-paste:

    mydummypiezo:
        module.Class: 'piezo.piezo_stage_dummy.PiezoStageDummy'
    """

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        pass

    # Initialization:
    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        print("Piezo Dummy activated.")

    # Operations:
    def move(self, direction):
        print("Piezo moved " + direction + ".")
        return 0

    # De-initialization:
    def on_deactivate(self):
        """ Deactivate the piezo dummy properly.
        """
        self.reset_hardware()

    def reset_hardware(self):
        """
        Reset the hardware, so the connection is lost and other programs can
        access it.

        @return int: error code: (0:OK, -1:error)
        """
        self.log.warning("Piezo Hardware will be reset.")
        return 0

    def close(self):
        """ Closes the hardware and cleans up afterwards.

        @return int: error code(0:OK, -1:error)
        """
        self.log.debug("PiezoStageDummy>close_controller")
        return 0
