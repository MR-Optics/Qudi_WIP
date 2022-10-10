# -*- coding: utf-8 -*-

"""
This module contains the Qudi interface file for controller - Not on GitHub right now.

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

from core.interface import abstract_interface_method
from core.meta import InterfaceMetaclass


class ControllerInterface(metaclass=InterfaceMetaclass):
    """
    This is the Interface class to define the controls for a piezo device.
    """

    @abstract_interface_method
    def move(self, direction):
        """
        Moves the hardware in direction.

        @return int: error code (0:OK, -1:error)
        """
        pass

    @abstract_interface_method
    def close(self):
        """ Closes the hardware and cleans up afterwards.

        @return  int: error code(0:OK, -1:error)
        """
        pass
