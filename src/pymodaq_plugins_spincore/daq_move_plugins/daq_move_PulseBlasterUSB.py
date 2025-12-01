from typing import Union, List, Dict
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base,
    comon_parameters_fun,
    main,
    DataActuatorType,
    DataActuator,
)

from pymodaq_utils.utils import (
    ThreadCommand,
)  # object used to send info back to the main thread
from pymodaq_gui.parameter import Parameter
from pymodaq_plugins_spincore.hardware.pulseblaster import PulseBlaster
from pymodaq_plugins_spincore.hardware._spinapi import SpinAPI
import numpy as np
import matplotlib.pyplot as plt


class DAQ_Move_PulseBlasterUSB(DAQ_Move_base):
    """Instrument plugin class for an actuator.

    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of controllers and actuators that should be compatible with this instrument plugin.
        * With which instrument and controller it has been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    # TODO add your particular attributes here if any

    """

    is_multiaxes = True
    _axis_names: Union[List[str], Dict[str, int]] = ["Laser", "MW"]
    _controller_units: Union[str, List[str]] = ""
    _epsilon: Union[float, List[float]] = 0.1
    data_actuator_type = DataActuatorType.DataActuator

    params = [
        {
            "title": "Channel",
            "name": "channel",
            "type": "list",
            "limits": [k for k in range(21)],
        },
        {"title": "Board Number", "name": "board_number", "type": "int", "value": 0},
        {
            "title": "Clock frequency",
            "name": "clock_frequency",
            "type": "list",
            "limits": [500],
        },
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: PulseBlaster = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        if self.controller.running:
            pos = DataActuator(data=np.array([1]), units=self.axis_unit)
        else:
            pos = DataActuator(data=np.array([0]), units=self.axis_unit)
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.shutdown()

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "board_number":
            self.controller.board_number = param.value()
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:  # is needed when controller is master
            self.controller = PulseBlaster(
                clock=self.settings.child("clock_frequency").value()
            )
            initialized = True  # our class PulseBlaster in it's function __init__ already checks if it's well initialized
        else:
            self.controller = controller
            initialized = True

        info = "Connected to PulseBlaster"
        return info, initialized

    def move_abs(self, value: DataActuator):
        """Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(
            value
        )  # if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(
            value
        )  # apply scaling if the user specified one
        if value.value() == 0:
            self.controller.stop()
            self.emit_status(
                ThreadCommand(
                    "Update_Status",
                    [f"Channel {self.settings.child('channel').value()} OFF"],
                )
            )
        elif value.value() == 1:
            laseron = [(1, 100)]
            self.controller.set_channel(self.settings.child("channel").value(), laseron)
            start = self.controller.compile_channels()
            self.controller.add_inst(0x000000, SpinAPI.BRANCH, start, 10)
            self.controller.program()
            # self.controller.reset()
            self.controller.start()
            self.emit_status(
                ThreadCommand(
                    "Update_Status",
                    [f"Channel {self.settings.child('channel').value()} ON"],
                )
            )

    def move_rel(self, value: DataActuator):
        """Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        ## TODO for your custom plugin
        raise NotImplementedError  # when writing your own plugin remove this line
        self.controller.your_method_to_set_a_relative_value(
            value.value(self.axis_unit)
        )  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand("Update_Status", ["Some info you want to log"]))

    def move_home(self):
        """Call the reference method of the controller"""

        ## TODO for your custom plugin
        raise NotImplementedError  # when writing your own plugin remove this line
        self.controller.your_method_to_get_to_a_known_reference()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand("Update_Status", ["Some info you want to log"]))

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.controller.stop()
        self.emit_status(
            ThreadCommand(
                "Update_Status",
                [f"Channel {self.settings.child('channel').value()} OFF"],
            )
        )


if __name__ == "__main__":
    main(__file__)
