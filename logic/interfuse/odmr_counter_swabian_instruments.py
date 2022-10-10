
import numpy as np
from time import sleep

from core.connector import Connector
from logic.generic_logic import GenericLogic
from interface.odmr_counter_interface import ODMRCounterInterface


class ODMRCounterSwabianInstruments(GenericLogic, ODMRCounterInterface):
    """ OMDR counter using the swabian timetagger and pulsestreamer."""

    timetagger = Connector(interface='SlowCounterInterface')
    pulse_streamer = Connector(interface='PulserInterface')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self._pulse_out_channel = 'dummy'
        self._lock_in_active = False
        self._oversampling = 10
        self._odmr_length = 100

    def on_activate(self):
        self.counter = self.timetagger()
        self.pulser = self.pulse_streamer()

    def on_deactivate(self):
        pass

    def set_up_odmr_clock(self, clock_frequency=None, clock_channel=None):
        self._omdr_frequency = clock_frequency
        return self.counter.set_up_clock(clock_frequency=clock_frequency, clock_channel=clock_channel)

    def set_up_odmr(self, counter_channel=None, photon_source=None,
                    clock_channel=None, odmr_trigger_channel=None):
        """ Configures the actual counter with a given clock.

        @param str counter_channel: if defined, this is the physical channel of
                                    the counter
        @param str photon_source: if defined, this is the physical channel where
                                  the photons are to count from
        @param str clock_channel: if defined, this specifies the clock for the
                                  counter
        @param str odmr_trigger_channel: if defined, this specifies the trigger
                                         output for the microwave

        @return int: error code (0:OK, -1:error)
        """
        self.counter.configure_ODMR_counter(self._odmr_length)
        self.pulser.ODMR_sequence(self._omdr_frequency, self._odmr_length)
        return 0


    def set_odmr_length(self, length=100):
        """Set up the trigger sequence for the ODMR and the triggered microwave.

        @param int length: length of microwave sweep in pixel

        @return int: error code (0:OK, -1:error)
        """
        self._odmr_length = length
        return 0

    def count_odmr(self, length = 100):
        """ Sweeps the microwave and returns the counts on that sweep.

        @param int length: length of microwave sweep in pixel

        @return (bool, float[]): tuple: was there an error, the photon counts per second
        """

        # TODO: set_up_odmr is running twice.. fix me
        self.set_odmr_length(length)
        self.set_up_odmr()

        self.counter.start_measure_sc()
        self.pulser.pulser_on()
        count_data = np.zeros((1, self._odmr_length))

        while not self.counter.is_array_filled():
            sleep(0.0001)

        self.counter.stop_measure_sc()
        bin_count_data, info = self.counter.get_data_trace_sc()

        count_data[0, :] = bin_count_data * self._omdr_frequency

        return False, count_data

    def close_odmr(self):
        """ Close the odmr and clean up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        self.pulser.pulser_off()
        return 0

    def close_odmr_clock(self):
        """ Close the odmr and clean up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        return 0

    def get_odmr_channels(self):
        """ Return a list of channel names.

        @return list(str): channels recorded during ODMR measurement
        """
        return self.counter.get_counter_channels()

    @property
    def oversampling(self):
        pass

    @oversampling.setter
    def oversampling(self, val):
        pass

    @property
    def lock_in_active(self):
        pass

    @lock_in_active.setter
    def lock_in_active(self, val):
        pass
