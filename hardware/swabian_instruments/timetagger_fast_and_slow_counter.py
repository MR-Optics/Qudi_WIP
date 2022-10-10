# -*- coding: utf-8 -*-
"""
A hardware module for communicating with the fast counter FPGA.

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

from interface.fast_counter_interface import FastCounterInterface
from interface.slow_counter_interface import SlowCounterInterface
from interface.slow_counter_interface import SlowCounterConstraints
from interface.slow_counter_interface import CountingMode
import numpy as np
import TimeTagger as tt
from core.module import Base
from core.configoption import ConfigOption
import os
import time


class TimeTaggerCounter(Base, FastCounterInterface, SlowCounterInterface):
    """ Hardware class to controls a Time Tagger from Swabian Instruments.

    Example config for copy-paste:

    fastcounter_timetagger:
        module.Class: 'swabian_instruments.timetagger_fast_counter.TimeTaggerFastCounter'
        timetagger_channel_apd_0: 0
        timetagger_channel_apd_1: 1
        timetagger_channel_detect: 2
        timetagger_channel_begin: 3
        timetagger_sum_channels: 4

    """
    pulsed = None

    _channel_apd_0 = ConfigOption('timetagger_channel_apd_0', missing='error')
    _channel_apd_1 = ConfigOption('timetagger_channel_apd_1', missing='warn')
    _channel_detect = ConfigOption('timetagger_channel_detect', missing='warn')
    _channel_sync = ConfigOption('timetagger_channel_sync', tt.CHANNEL_UNUSED , missing='warn')
    _channel_begin = ConfigOption('timetagger_channel_begin', missing='warn')
    _sum_channels = ConfigOption('timetagger_sum_channels', False, missing='warn')

    def on_activate(self):
        """ Connect and configure the access to the FPGA.
        """
        self._tagger = tt.createTimeTagger()
        self._tagger.reset()
        self._count_frequency = 50  # Hz

        self._number_of_gates = int(100)
        self._bin_width = 1
        self._record_length = int(4000)

        if self._sum_channels:
            self._channel_combined = tt.Combiner(self._tagger, channels=[self._channel_apd_0, self._channel_apd_1])
            self._channel_apd = self._channel_combined.getChannel()
        else:
            self._channel_apd = self._channel_apd_0

        self.log.info('TimeTagger (fast counter) configured to use  channel {0}'
                      .format(self._channel_apd))

        if self._sum_channels and self._channel_apd_1 is None:
            self.log.error('Cannot sum channels when only one apd channel given')
        # For slow counter
        if self._sum_channels:
            self._mode = 1
        elif self._channel_apd_1 is None:
            self._mode = 0
        else:
            self._mode = 2

        self.statusvar = 0

    @FastCounterInterface.get_constraints.register('FastCounterInterface')
    def get_constraints_fc(self):
        """ Retrieve the hardware constrains from the Fast counting device.

        @return dict: dict with keys being the constraint names as string and
                      items are the definition for the constaints.

         The keys of the returned dictionary are the str name for the constraints
        (which are set in this method).

                    NO OTHER KEYS SHOULD BE INVENTED!

        If you are not sure about the meaning, look in other hardware files to
        get an impression. If still additional constraints are needed, then they
        have to be added to all files containing this interface.

        The items of the keys are again dictionaries which have the generic
        dictionary form:
            {'min': <value>,
             'max': <value>,
             'step': <value>,
             'unit': '<value>'}

        Only the key 'hardware_binwidth_list' differs, since they
        contain the list of possible binwidths.

        If the constraints cannot be set in the fast counting hardware then
        write just zero to each key of the generic dicts.
        Note that there is a difference between float input (0.0) and
        integer input (0), because some logic modules might rely on that
        distinction.

        ALL THE PRESENT KEYS OF THE CONSTRAINTS DICT MUST BE ASSIGNED!
        """

        constraints = dict()

        # the unit of those entries are seconds per bin. In order to get the
        # current binwidth in seonds use the get_binwidth method.
        constraints['hardware_binwidth_list'] = [1 / 1000e6, 0.5e-7, 1e-7, 1e-6, 50e-6, 1e-4, 2e-4, 1e-3, 5e-3, 10e-3]

        # TODO: think maybe about a software_binwidth_list, which will
        #      postprocess the obtained counts. These bins must be integer
        #      multiples of the current hardware_binwidth

        return constraints

    def on_deactivate(self):
        """ Deactivate the FPGA.
        """
        if self.module_state() == 'locked' and self.pulsed is not None:
            self.pulsed.stop()
            self.pulsed.clear()
            self.pulsed = None

    def configure(self, bin_width_s, record_length_s, number_of_gates=0):

        """ Configuration of the fast counter.

        @param float bin_width_s: Length of a single time bin in the time trace
                                  histogram in seconds.
        @param float record_length_s: Total length of the timetrace/each single
                                      gate in seconds.
        @param int number_of_gates: optional, number of gates in the pulse
                                    sequence. Ignore for not gated counter.

        @return tuple(binwidth_s, gate_length_s, number_of_gates):
                    binwidth_s: float the actual set binwidth in seconds
                    gate_length_s: the actual set gate length in seconds
                    number_of_gates: the number of gated, which are accepted
        """
        self._number_of_gates = number_of_gates
        self._bin_width = bin_width_s * 1e9
        self._record_length = int(record_length_s / bin_width_s)
        self.statusvar = 1

        self.pulsed = tt.TimeDifferences(
            tagger=self._tagger,
            click_channel=self._channel_apd,
            start_channel=self._channel_detect,
            next_channel=self._channel_detect,
            sync_channel=self._channel_sync,
            binwidth=int(np.round(self._bin_width * 1000)),
            n_bins=int(self._record_length),
            n_histograms=number_of_gates)

        self.pulsed.stop()

        return bin_width_s, record_length_s, number_of_gates

    @FastCounterInterface.start_measure.register('FastCounterInterface')
    def start_measure_fc(self):
        """ Start the fast counter. """
        self.module_state.lock()
        self.pulsed.clear()
        self.pulsed.start()
        self.statusvar = 2
        return 0

    @FastCounterInterface.stop_measure.register('FastCounterInterface')
    def stop_measure_fc(self):
        """ Stop the fast counter. """
        if self.module_state() == 'locked' and self.pulsed is not None:
            self.pulsed.stop()
            self.pulsed.clear()
            self.module_state.unlock()
        self.statusvar = 1
        return 0

    @FastCounterInterface.pause_measure.register('FastCounterInterface')
    def pause_measure_fc(self):
        """ Pauses the current measurement.

        Fast counter must be initially in the run state to make it pause.
        """
        if self.module_state() == 'locked':
            self.pulsed.stop()
            self.statusvar = 3
            self.module_state.unlock()
        return 0

    @FastCounterInterface.continue_measure.register('FastCounterInterface')
    def continue_measure_fc(self):
        """ Continues the current measurement.

        If fast counter is in pause state, then fast counter will be continued.
        """
        if self.module_state() == 'idle':
            self.module_state.lock()

        if self.module_state() == 'locked':
            self.pulsed.start()
            self.statusvar = 2
        return 0

    def configure_count_between_markers(self, number_of_gates=0):

        """ Configuration of gated counter.

                                      gate in seconds.
        @param int number_of_gates: optional, number of gates in the pulse
                                    sequence. Ignore for not gated counter.

        @return tuple(binwidth_s, gate_length_s, number_of_gates):
                    binwidth_s: float the actual set binwidth in seconds
                    gate_length_s: the actual set gate length in seconds
                    number_of_gates: the number of gated, which are accepted
        """
        self._number_of_gates = number_of_gates

        self.count_between_markers = tt.CountBetweenMarkers(
            tagger=self._tagger,
            click_channel=self._channel_apd,
            begin_channel=self._channel_begin,
            n_values=number_of_gates)

        self.count_between_markers.stop()

        return number_of_gates


    def start_measure_sc(self):
        """ Start the fast counter. """
        self.module_state.lock()
        self.count_between_markers.clear()
        self.count_between_markers.start()
        self.statusvar = 2
        return 0


    def stop_measure_sc(self):
        """ Stop the fast counter. """
        if self.module_state() == 'locked':
            self.count_between_markers.stop()
            self.module_state.unlock()
        self.statusvar = 1
        return 0


    def pause_measure_sc(self):
        """ Pauses the current measurement.

        Fast counter must be initially in the run state to make it pause.
        """
        if self.module_state() == 'locked':
            self.count_between_markers.stop()
            self.statusvar = 3
        return 0

    def continue_measure_sc(self):
        """ Continues the current measurement.

        If fast counter is in pause state, then fast counter will be continued.
        """
        if self.module_state() == 'locked':
            self.count_between_markers.start()
            self.statusvar = 2
        return 0

    def get_data_trace_sc(self):
        """ Polls the current timetrace data from the fast counter.

        @return numpy.array: 2 dimensional array of dtype = int64. This counter
                             is gated the the return array has the following
                             shape:
                                returnarray[gate_index, timebin_index]

        The binning, specified by calling configure() in forehand, must be taken
        care of in this hardware class. A possible overflow of the histogram
        bins must be caught here and taken care of.
        """
        info_dict = {'elapsed_sweeps': None,
                     'elapsed_time': None}  # TODO : implement that according to hardware capabilities
        return np.array(self.count_between_markers.getData(), dtype='int64'), info_dict

    def is_gated(self):
        """ Check the gated counting possibility.

        Boolean return value indicates if the fast counter is a gated counter
        (TRUE) or not (FALSE).
        """
        return True

    def get_data_trace(self):
        """ Polls the current timetrace data from the fast counter.

        @return numpy.array: 2 dimensional array of dtype = int64. This counter
                             is gated the the return array has the following
                             shape:
                                returnarray[gate_index, timebin_index]

        The binning, specified by calling configure() in forehand, must be taken
        care of in this hardware class. A possible overflow of the histogram
        bins must be caught here and taken care of.
        """
        info_dict = {'elapsed_sweeps': None,
                     'elapsed_time': None}  # TODO : implement that according to hardware capabilities
        return np.array(self.pulsed.getData(), dtype='int64'), info_dict


    def get_status(self):
        """ Receives the current status of the Fast Counter and outputs it as
            return value.

        0 = unconfigured
        1 = idle
        2 = running
        3 = paused
        -1 = error state
        """
        return self.statusvar

    def get_binwidth(self):
        """ Returns the width of a single timebin in the timetrace in seconds. """
        width_in_seconds = self._bin_width * 1e-9
        return width_in_seconds

    def is_array_filled(self):
        return self.count_between_markers.ready()

    ############ SLOW COUNTER INTERFACE
    def set_up_clock(self, clock_frequency=None, clock_channel=None):
        """ Configures the hardware clock of the TimeTagger for timing

        @param float clock_frequency: if defined, this sets the frequency of
                                      the clock
        @param string clock_channel: if defined, this is the physical channel
                                     of the clock

        @return int: error code (0:OK, -1:error)
        """

        self._count_frequency = clock_frequency
        return 0

    def set_up_counter(self,
                       counter_channels=None,
                       sources=None,
                       clock_channel=None,
                       counter_buffer=None):
        """ Configures the actual counter with a given clock.

        @param str counter_channel: optional, physical channel of the counter
        @param str photon_source: optional, physical channel where the photons
                                  are to count from
        @param str counter_channel2: optional, physical channel of the counter 2
        @param str photon_source2: optional, second physical channel where the
                                   photons are to count from
        @param str clock_channel: optional, specifies the clock channel for the
                                  counter
        @param int counter_buffer: optional, a buffer of specified integer
                                   length, where in each bin the count numbers
                                   are saved.

        @return int: error code (0:OK, -1:error)
        """

        # currently, parameters passed to this function are ignored -- the channels used and clock frequency are
        # set at startup
        if self._mode == 1:
            channel_combined = tt.Combiner(self._tagger, channels = [self._channel_apd_0, self._channel_apd_1])
            self._channel_apd = channel_combined.getChannel()

            self.counter = tt.Counter(
                self._tagger,
                channels=[self._channel_apd],
                binwidth=int((1 / self._count_frequency) * 1e12),
                n_values=1
            )
        elif self._mode == 2:
            self.counter0 = tt.Counter(
                self._tagger,
                channels=[self._channel_apd_0],
                binwidth=int((1 / self._count_frequency) * 1e12),
                n_values=1
            )

            self.counter1 = tt.Counter(
                self._tagger,
                channels=[self._channel_apd_1],
                binwidth=int((1 / self._count_frequency) * 1e12),
                n_values=1
            )
        else:
            self._channel_apd = self._channel_apd_0
            self.counter = tt.Counter(
                self._tagger,
                channels=[self._channel_apd],
                binwidth=int((1 / self._count_frequency) * 1e12),
                n_values=1
            )

        self.log.info('set up counter with {0}'.format(self._count_frequency))
        self.counter.start()
        return 0

    def get_counter_channels(self):
        if self._mode < 2:
            return [self._channel_apd]
        else:
            return [self._channel_apd_0, self._channel_apd_1]

    @SlowCounterInterface.get_constraints.register('SlowCounterInterface')
    def get_constraints_sc(self):
        """ Get hardware limits the device

        @return SlowCounterConstraints: constraints class for slow counter

        FIXME: ask hardware for limits when module is loaded
        """
        constraints = SlowCounterConstraints()
        constraints.max_detectors = 2
        constraints.min_count_frequency = 1e-3
        constraints.max_count_frequency = 10e9
        constraints.counting_mode = [CountingMode.CONTINUOUS]
        return constraints


    def get_counter(self, samples=None):
        """ Returns the current counts per second of the counter.

        @param int samples: if defined, number of samples to read in one go

        @return numpy.array(uint32): the photon counts per second
        """

        time.sleep(1/(self._count_frequency))

        if self._mode < 2:
            return self.counter.getData() * self._count_frequency
        else:
            return np.array([self.counter0.getData() * self._count_frequency,
                             self.counter1.getData() * self._count_frequency])

    def close_counter(self):
        """ Closes the counter and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        if self._mode < 2:
            self.counter.clear()
        else:
            self.counter0.clear()
            self.counter1.clear()
        return 0

    def close_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        return 0

    def configure_ODMR_counter(self, number_of_gates=0):

        """ Configuration of gated counter.

                                      gate in seconds.
        @param int number_of_gates: optional, number of gates in the pulse
                                    sequence. Ignore for not gated counter.

        @return tuple(binwidth_s, gate_length_s, number_of_gates):
                    binwidth_s: float the actual set binwidth in seconds
                    gate_length_s: the actual set gate length in seconds
                    number_of_gates: the number of gated, which are accepted
        """
        self._number_of_gates = number_of_gates

        self.count_between_markers = tt.CountBetweenMarkers(
            tagger=self._tagger,
            click_channel=self._channel_apd,
            begin_channel=self._channel_detect,
            n_values=number_of_gates)

        self.count_between_markers.stop()

        return number_of_gates

