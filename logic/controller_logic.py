# -*- coding: utf-8 -*-
"""
This module operates a piezo-stage - Not on GitHub right now.

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

from qtpy import QtCore
from collections import OrderedDict
from copy import copy
import time
import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from core.connector import Connector
from core.statusvariable import StatusVar


class ControllerLogic(GenericLogic):
    """
    This is the Logic class for piezo-stage movements.

    Example: config for copy-paste:

    controllerlogic:
        module.Class: 'controller_logic.ControllerLogic'
        connect:
            controller1: 'controller_piezo_interfuse'

    """

    # declare connectors
    controller1 = Connector(interface='ControllerInterface')

    # status vars

    # signals
    signal_move_forward = QtCore.Signal(str)
    signal_move_backward = QtCore.Signal(str)
    signal_move_left = QtCore.Signal(str)
    signal_move_right = QtCore.Signal(str)


    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        # locking for thread safety
        self.threadlock = Mutex()

    # Initialization:
    def on_activate(self):
        """ Initialization performed during activation of the module.
        """
        self._controller = self.controller1()
        pass

        # Sets connections between signals and functions
        self.signal_move_forward.connect(self.move_forward, QtCore.Qt.QueuedConnection)
        self.signal_move_backward.connect(self.move_backward, QtCore.Qt.QueuedConnection)
        self.signal_move_left.connect(self.move_left, QtCore.Qt.QueuedConnection)
        self.signal_move_right.connect(self.move_right, QtCore.Qt.QueuedConnection)

    # De-initialization:
    def on_deactivate(self):
        """ Reverse steps of activation.
        """

        return 0

    # Operations:
    def move_forward(self, tag='logic'):
        self._controller.move("forward")

    def move_backward(self, tag='logic'):
        self._controller.move("backward")

    def move_left(self, tag='logic'):
        self._controller.move("left")

    def move_right(self, tag='logic'):
        self._controller.move("right")

        pass
