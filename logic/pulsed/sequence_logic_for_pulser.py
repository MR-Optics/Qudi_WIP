import datetime
import numpy as np
import time

from collections import OrderedDict
from core.connector import Connector
from core.statusvariable import StatusVar
from core.util.mutex import Mutex
from logic.generic_logic import GenericLogic
from interface.pulser_interface import PulserInterface, PulserConstraints
from logic.pulsed.pulse_objects import PulseBlock, PulseBlockEnsemble, PulseSequence
from qtpy import QtCore


class SequenceLogicForPulser(GenericLogic, PulserInterface):
    """
    Handle the pulser sequence for pulser without internal memory.

    Connects to scanner and optimizaer to do periodical optimization of the position.

    Example config for copy-paste:

    sequence_pulser_logic:
        module.Class: 'pulsed.sequence_logic_for_pulser.SequenceLogicForPulser'
        connect:
            pulsegenerator: 'pulsestreamer'
            optimizerlogic: 'optimizerlogic'
            scannerlogic: 'scannerlogic'
    """

    pulsegenerator = Connector(interface='PulserInterface')
    # FIXME: THESE CONNECTORS SHOULD NOT BE IN THIS FILE!!!
    optimizerlogic = Connector(interface='OptimizerLogic')
    scannerlogic = Connector(interface='ConfocalLogic')

    _current_loaded_sequence = ''
    _sequence_list = OrderedDict()
    _run_mode = 'waveform'

    sigMeasStarted = QtCore.Signal()
    sigNextMeasPoint = QtCore.Signal()
    sigCurrMeasPointUpdated = QtCore.Signal()
    sigMeasurementStopped = QtCore.Signal(str)
    sigPauseMeasurement = QtCore.Signal(bool)
    sigPulserOff = QtCore.Signal()


    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.debug('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key,config[key]))

        self.threadlock = Mutex()

    def on_activate(self):

        self.pulse_generator = self.pulsegenerator()
        self._optimizer_logic = self.optimizerlogic()
        self._confocal_logic = self.scannerlogic()
        self.sigNextMeasPoint.connect(self._seq_loop_measurement, QtCore.Qt.QueuedConnection)
        self.sigMeasurementStopped.connect(self.stop_seq_measurement, QtCore.Qt.QueuedConnection)
        self.optimize_period = 5 # s
        self._optimizer_is_running = False
        self._optimizer_logic.sigRefocusFinished.connect(self.wait_for_optimizer)

    def on_deactivate(self):
        pass

    def get_constraints(self):
        return self.pulse_generator.get_constraints()

    def pulser_on(self):
        if self._run_mode == 'waveform':
            return self.pulse_generator.pulser_on()
        else:
             self.start_seq_measurement()
        return 0

    def pulser_off(self):
        if self._run_mode == 'waveform':
            self.sigPulserOff.emit()
            return self.pulse_generator.pulser_off()
        else:
            return self.stop_seq_measurement()

    def pulser_continue(self):
        if self._run_mode == 'waveform':
            return self.pulse_generator.pulser_on()
        else:
            self.continue_seq_measurement()
        return 0

    def pulser_pause(self):
        if self._run_mode == 'waveform':
            return self.pulse_generator.pulser_off()
        else:
            return self.pause_seq_measurement()

    def load_waveform(self, load_dict):
        self._run_mode = 'waveform'
        return self.pulse_generator.load_waveform(load_dict=load_dict)

    def get_loaded_assets(self):
        if self._run_mode == 'waveform':
            return self.pulse_generator.get_loaded_assets()
        else:
            asset_dict = {chnl_num: self._current_loaded_sequence for chnl_num in range(1, 9)}
            asset_type = 'sequence'
            return asset_dict, asset_type

    def clear_all(self):
        return self.pulse_generator.clear_all()

    def get_status(self):
        return self.pulse_generator.get_status()

    def get_sample_rate(self):
        return self.pulse_generator.get_sample_rate()

    def set_sample_rate(self, sample_rate):
        return self.pulse_generator.set_sample_rate(sample_rate=sample_rate)

    def get_analog_level(self, amplitude=None, offset=None):
        return self.pulse_generator.get_analog_level(amplitude=amplitude, offset=offset)

    def set_analog_level(self, amplitude=None, offset=None):
        return self.pulse_generator.set_analog_level(amplitude=amplitude, offset=offset)

    def get_digital_level(self, low=None, high=None):
        return self.pulse_generator.get_digital_level(low=low, high=high)

    def set_digital_level(self, low=None, high=None):
        return self.pulse_generator.set_digital_level(low=low, high=high)

    def get_active_channels(self, ch=None):
        return self.pulse_generator.get_active_channels(ch=ch)

    def set_active_channels(self, ch=None):
        return self.set_active_channels(ch=ch)

    def write_waveform(self, name, analog_samples, digital_samples, is_first_chunk, is_last_chunk,
                       total_number_of_samples):

       return self.pulse_generator.write_waveform(name, analog_samples, digital_samples, is_first_chunk, is_last_chunk,
                       total_number_of_samples)

    def get_waveform_names(self):
        return self.pulse_generator.get_waveform_names()

    def get_interleave(self):
        return self.pulse_generator.get_interleave()

    def set_interleave(self, state=False):
        return self.pulse_generator.set_interleave(state)

    def reset(self):
        return self.pulse_generator.reset()

    def constant_output(self, active_channels=[], analog_values=[0,0]):
        return self.pulse_generator.constant_output(active_channels,analog_values)

    def change_laser_channel(self, channel):
        return self.pulse_generator.change_laser_channel(channel)

    def load_sequence(self, sequence_name):

        if sequence_name not in self.get_sequence_names():
            self.log.error('Unable to load sequence.\n'
                           'Sequence to load is missing on device memory.')
            return self.get_loaded_assets()

        self._run_mode = 'sequence'
        self._current_loaded_sequence = sequence_name

        return 0

    def delete_waveform(self, waveform_name):
        return self.pulse_generator.delete_waveform(waveform_name)

    def write_sequence(self, name, sequence_parameters):
        """
        Write a new sequence on the device memory.

        @param str name: the name of the waveform to be created/append to
        @param list sequence_parameters: List containing tuples of length 2. Each tuple represents
                                         a sequence step. The first entry of the tuple is a list of
                                         waveform names (str); one for each channel. The second
                                         tuple element is a SequenceStep instance containing the
                                         sequencing parameters for this step.

        @return: int, number of sequence steps written (-1 indicates failed process)
        """
        # Check if all waveforms are present on device memory
        avail_waveforms = set(self.get_waveform_names())
        for waveform_tuple, param_dict in sequence_parameters:
            if not avail_waveforms.issuperset(waveform_tuple):
                self.log.error('Failed to create sequence "{0}" due to waveforms "{1}" not '
                               'present in device memory.'.format(name, waveform_tuple))
                return -1

        num_steps = len(sequence_parameters)

        if name in self.get_sequence_names():
            self.delete_sequence(name)
        self._sequence_list[name] = sequence_parameters

        return num_steps

    def get_sequence_names(self):
        """ Retrieve the names of all uploaded sequence on the device.

        @return list: List of all uploaded sequence name strings in the device workspace.
        """

        sequence_list = list(self._sequence_list.keys())

        return sequence_list

    def delete_sequence(self, sequence_name):
        """ Delete the sequence with name "sequence_name" from the device memory.

        @param str sequence_name: The name of the sequence to be deleted
                                  Optionally a list of sequence names can be passed.

        @return list: a list of deleted sequence names.
        """
        del self._sequence_list[sequence_name]
        return

    def start_seq_measurement(self):
        """ Start the nuclear operation measurement. """

        self._stop_requested = False

        if self._run_mode != 'sequence':
            self.log.error('Sequence is not loaded')
            return -1

        self.module_state.lock()

        self.elapsed_time = 0
        self.next_optimize_time = 0 + self.optimize_period
        self.start_time = datetime.datetime.now()
        self.seq_step = 0
        self.no_of_steps = len(self._sequence_list[self._current_loaded_sequence])

        self.sigMeasStarted.emit()
        self.sigNextMeasPoint.emit()

    def _seq_loop_measurement(self):
        """ Run this loop continuously until the an abort criterium is reached. """

        with self.threadlock:
            self.log.info(self._stop_requested)
            if self._stop_requested:
                # end measurement and switch all devices off
                self._stop_requested = False
                # emit all needed signals for the update:
                self.sigCurrMeasPointUpdated.emit()
                return 0

        self.elapsed_time = (datetime.datetime.now() - self.start_time).total_seconds()

        #optimizise
        if self.next_optimize_time < self.elapsed_time:

            # perform  optimize position:
            self.sigPauseMeasurement.emit(True)
            self._laser_on()
            self._optimizer_is_running = True
            self._do_optimize_pos()

            # TODO: fix hardcoding
            time.sleep(10)

            self.elapsed_time = (datetime.datetime.now() - self.start_time).total_seconds()
            self.next_optimize_time = self.elapsed_time + self.optimize_period
            self.sigPauseMeasurement.emit(False)

            return


        ensemble_info = self._sequence_list[self._current_loaded_sequence][self.seq_step][1]
        waveform_in_seq_step = ensemble_info.ensemble
        no_rep_in_seq_step = ensemble_info.repetitions

        self.pulse_generator.load_waveform_from_memory(waveform_in_seq_step)
        self.pulse_generator.n_runs = no_rep_in_seq_step + 1 # so 0 repetations means run 1 time

        self.pulse_generator.pulser_on()

        retval = self.pulse_generator.is_pulser_seq_done()

        self.seq_step += 1
        if self.seq_step < self.no_of_steps:
            self.log.info(f'Step {self.seq_step} out of {self.no_of_steps}')
            self.sigCurrMeasPointUpdated.emit()
        else:
            self.log.info(f'Step {self.seq_step} out of {self.no_of_steps}')
            self.sigMeasurementStopped.emit('')
            time.sleep(5)


        self.sigNextMeasPoint.emit()

    def stop_seq_measurement(self):
        """ Stop the Nuclear Operation Measurement.

        @return int: error code (0:OK, -1:error)
        """


        if self.module_state() == 'locked':
            self._stop_requested = True
            self.module_state.unlock()

        self.pulse_generator.pulser_off()
        self.pulse_generator.n_runs = 1
        self.pulse_generator.pulser_done.set()
        return 0

    def pause_seq_measurement(self):
        """ Stop the Nuclear Operation Measurement.

        @return int: error code (0:OK, -1:error)
        """

        if self.module_state() == 'locked':
            self._stop_requested = True

        self.pulse_generator.pulser_off()
        self.pulse_generator.n_runs = 1
        self.pulse_generator.pulser_done.set()
        return 0

    def continue_seq_measurement(self):
        """ Start the nuclear operation measurement. """

        self._stop_requested = False

        if self._run_mode != 'sequence':
            self.log.error('Sequence is not loaded')
            return -1

        if self.module_state() == 'locked':
            self.sigNextMeasPoint.emit()
            return 0

    def _laser_on(self):
        self.pulse_generator.pulser_on()
        return self.pulse_generator.turn_on_laser()

    def _do_optimize_pos(self):
        curr_pos = self._confocal_logic.get_position()

        self._optimizer_logic.start_refocus(curr_pos, caller_tag='swabian_logic')

        # check just the state of the optimizer

        while self._optimizer_logic.module_state() != 'idle':
            time.sleep(0.5)

        # use the position to move the scanner
        self._confocal_logic.set_position('swabian_logic',
                                          self._optimizer_logic.optim_pos_x,
                                          self._optimizer_logic.optim_pos_y,
                                          self._optimizer_logic.optim_pos_z)

        return 0

    def wait_for_optimizer(self, string, list):

        self._optimizer_is_running = False

        return 0

