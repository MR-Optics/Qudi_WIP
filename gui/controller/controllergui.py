# -*- coding: utf-8 -*-

"""
This file contains the Qudi GUI for manual control - Not on GitHub right now.

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
import os
import pyqtgraph as pg
import time

from core.connector import Connector
from core.configoption import ConfigOption
from core.statusvariable import StatusVar
from qtwidgets.scan_plotwidget import ScanImageItem
from gui.guibase import GUIBase
from gui.guiutils import ColorBar
from gui.colordefs import ColorScaleInferno
from gui.colordefs import QudiPalettePale as palette
from gui.fitsettings import FitParametersWidget
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic


class ControllerMainWindow(QtWidgets.QMainWindow):
    """ Create the Mainwindow based on the corresponding *.ui file. """

    sigPressKeyBoard = QtCore.Signal(QtCore.QEvent)
    sigDoubleClick = QtCore.Signal()

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_controllergui.ui')
        self._doubleclicked = False

        # Load it
        super(ControllerMainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()

    def keyPressEvent(self, event):
        """Pass the keyboard press event from the main window further. """
        self.sigPressKeyBoard.emit(event)

    def mouseDoubleClickEvent(self, event):
        self._doubleclicked = True
        self.sigDoubleClick.emit()


class ControllerGui(GUIBase):
    """ Main Controller Class for manually controlling equipment.

    Example: config for copy-paste:

    controller:
        module.Class: 'controller.controllergui.ControllerGui'
        connect:
            controllerlogic1: 'controllerlogic'
    """

    # declare connectors
    controllerlogic1 = Connector(interface='ControllerLogic')

    def __init__(self, config, **kwargs):
        # load connection
        super().__init__(config=config, **kwargs)

    # Initialization:
    def on_activate(self):
        """ Initializes all the needed UI files and establishes the connectors.
        """

        # Getting access to all connectors:
        self._controller_logic = self.controllerlogic1()

        self.initMainUI()

    def initMainUI(self):
        self._mw = ControllerMainWindow()

        ###################################################################
        #               Configuring the dock widgets                      #
        ###################################################################
        # All our gui elements are dockable, and so there should be no
        # "central" widget.
        self._mw.centralwidget.hide()
        self._mw.setDockNestingEnabled(True)

        self._hardware_state = True

        #################################################################
        #                           Actions                             #
        #################################################################
        # Connect the move actions to the events if they are clicked.

        self._move_forward_proxy = pg.SignalProxy(
            self._mw.actionForward.triggered,
            delay=0.01,
            slot=self.move_forward_clicked
        )

        self._move_backward_proxy = pg.SignalProxy(
            self._mw.actionBackward.triggered,
            delay=0.01,
            slot=self.move_backward_clicked
        )

        self._move_left_proxy = pg.SignalProxy(
            self._mw.actionLeft.triggered,
            delay=0.01,
            slot=self.move_left_clicked
        )

        self._move_right_proxy = pg.SignalProxy(
            self._mw.actionRight.triggered,
            delay=0.01,
            slot=self.move_right_clicked
        )

        self.show()

    def show(self):
        """Make main window visible and put it above all other windows. """
        # Show the Main Confocal GUI:
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    # De-initialization:
    def on_deactivate(self):
        """ Reverse the steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    # Operations:
    def move_forward_clicked(self):
        """ Manages what happens if the forward button is pressed. """
        self._controller_logic.move_forward(tag='gui')

    def move_backward_clicked(self):
        """ Manages what happens if the backward button is pressed. """
        self._controller_logic.move_backward(tag='gui')

    def move_left_clicked(self):
        """ Manages what happens if the up button is pressed. """
        self._controller_logic.move_left(tag='gui')

    def move_right_clicked(self):
        """ Manages what happens if the up button is pressed. """
        self._controller_logic.move_right(tag='gui')
