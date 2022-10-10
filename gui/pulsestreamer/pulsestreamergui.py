import os

from core.connector import Connector
from gui.guibase import GUIBase
from qtpy import QtWidgets
from qtpy import QtCore
from qtpy import uic


class PulserMainWindow(QtWidgets.QMainWindow):
    """ Helper class for window loaded from UI file.
    """
    def __init__(self):
        """ Create the switch GUI window.
        """
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_output.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()


class pulsestreamerGui(GUIBase):
    """ A grephical interface to mofe switches by hand and change their calibration.
    """

    # declare connectors
    pulsestreamer = Connector(interface='SequenceLogicForPulser')
    sigOutputChanged = QtCore.Signal()



    def on_activate(self):
        """Create all UI objects and show the window.
        """
        self.pulse_logic = self.pulsestreamer()

        self.pulse_logic.sigPulserOff.connect(self.off)

        self._mw = PulserMainWindow()

        self._mw.checkBox_1.clicked.connect(self.change_output)
        self._mw.checkBox_2.clicked.connect(self.change_output)
        self._mw.checkBox_3.clicked.connect(self.change_output)
        self._mw.checkBox_4.clicked.connect(self.change_output)
        self._mw.checkBox_5.clicked.connect(self.change_output)
        self._mw.checkBox_6.clicked.connect(self.change_output)
        self._mw.checkBox_7.clicked.connect(self.change_output)
        self._mw.checkBox_8.clicked.connect(self.change_output)
        self._mw.doubleSpinBox_AO0.valueChanged.connect(self.change_output)
        self._mw.doubleSpinBox_AO0.valueChanged.connect(self.change_output)

        self._mw.checkBox_9.clicked.connect(self.change_laser_channel4)
        self._mw.checkBox_10.clicked.connect(self.change_laser_channel1)
        self._mw.checkBox_11.clicked.connect(self.change_laser_channel5)


        self.checkBox_list = [self._mw.checkBox_1,
                              self._mw.checkBox_2,
                              self._mw.checkBox_3,
                              self._mw.checkBox_4,
                              self._mw.checkBox_5,
                              self._mw.checkBox_6,
                              self._mw.checkBox_7,
                              self._mw.checkBox_8]

        self.checkBox_list2 = [self._mw.checkBox_9,
                              self._mw.checkBox_10,
                              self._mw.checkBox_11]


        self.restoreWindowPos(self._mw)
        self.show()

        self.sigOutputChanged.connect(self.change_output)

    def change_output(self):
        """ Invert the state of the switch associated with this widget.
        """
        active_channels = []
        for channel in range(8):
            if self.checkBox_list[channel].isChecked():
                active_channels.append(channel)

        analog_values = [self._mw.doubleSpinBox_AO0.value(), self._mw.doubleSpinBox_AO1.value()]


        self.pulse_logic.constant_output(active_channels=active_channels, analog_values=analog_values)

    def change_laser_channel4(self):

        active_laser_channel = int(4)
        self.checkBox_list2[1].setChecked(False)
        self.checkBox_list2[2].setChecked(False)

        self.pulse_logic.change_laser_channel(active_laser_channel)

    def change_laser_channel1(self):

        active_laser_channel = int(0)
        self.checkBox_list2[0].setChecked(False)
        self.checkBox_list2[2].setChecked(False)

        self.pulse_logic.change_laser_channel(active_laser_channel)

    def change_laser_channel5(self):

        active_laser_channel = int(5)
        self.checkBox_list2[0].setChecked(False)
        self.checkBox_list2[1].setChecked(False)

        self.pulse_logic.change_laser_channel(active_laser_channel)

    def show(self):
        """Make sure that the window is visible and at the top.
        """
        self._mw.show()

    def on_deactivate(self):
        """ Hide window and stop ipython console.
        """
        self.saveWindowPos(self._mw)
        self._mw.close()

    def off(self):
        for channel in range(8):
            self.checkBox_list[channel].setChecked(False)

        return

