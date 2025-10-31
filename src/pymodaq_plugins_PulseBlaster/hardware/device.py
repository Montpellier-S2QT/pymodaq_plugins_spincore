"""
PulseBlaster device interface for programming and controlling the hardware.

This module provides a Python interface to the SpinCore PulseBlaster board
for programming instruction sequences and controlling execution.
"""

from typing import Sequence

import numpy as np
from pymodaq_plugins_PulseBlaster.hardware.spinapi import (
    PULSE_PROGRAM,
    ns,
    pb_core_clock,
    pb_get_error,
    pb_get_firmware_id,
    pb_get_version,
    pb_init,
    pb_inst_pbonly,
    pb_read_status,
    pb_reset,
    pb_select_board,
    pb_start,
    pb_start_programming,
    pb_stop_programming,
    pb_stop,
    pb_close,
)

from pymodaq_plugins_PulseBlaster.hardware.data_structures import Instruction


class PulseBlaster:
    def __init__(
        self,
        board_number: int,
        clock: int = 500,
    ):
        self._board_number = board_number
        self._clock = clock

        pb_select_board(board_number)
        if pb_init() != 0:
            raise ConnectionError(
                f"Could not initialize PulseBlaster board {board_number}"
            )

    @property
    def board_number(self) -> int:
        """
        Board number

        Returns:
            int: board number
        """
        return self._board_number

    @board_number.setter
    def board_number(self, value):
        self._board_number = value
        pb_select_board(value)
        if pb_init() != 0:
            raise ConnectionError(f"Could not initialize PulseBlaster board {value}")

    @property
    def clock(self) -> int:
        """
        Clock speed [MHz]

        Returns:
            int: clock speed [MHz]
        """
        return self._clock

    @property
    def firmware_id(self) -> int:
        return pb_get_firmware_id()

    @property
    def version(self) -> str:
        return pb_get_version()

    @property
    def error(self) -> str:
        """
        Most recent error string

        Returns:
            str: error
        """
        return pb_get_error()

    @property
    def status(self) -> int:
        """
        Read status (4 bits)
        bit 0 - stopped
        bit 1 - reset
        bit 2 - running
        bit 3 - waiting

        Returns:
            int: status bit
        """
        return pb_read_status()

    def program(self, sequence: Sequence[Instruction]) -> None:
        """
        Program the PulseBlaster with a sequence of instructions.

        Args:
            sequence (Sequence[Instruction]): sequence of instructions to program
        """
        pb_reset()
        pb_core_clock(self.clock)
        pb_start_programming(PULSE_PROGRAM)

        for seq in sequence:
            flags_int = int(
                np.sum([1 << i if v else 0 for i, v in enumerate(seq.flags)])
            )
            print("flags:", flags_int)
            print("opcode:", seq.opcode)
            print("inst_data:", seq.inst_data)
            print("duree:", seq.duration * ns)

            pb_inst_pbonly(flags_int, seq.opcode, seq.inst_data, seq.duration * ns)
        pb_stop_programming()

    def start(self) -> None:
        """Start the PulseBlaster program execution."""
        pb_start()

    def reset(self) -> None:
        """Reset the PulseBlaster board."""
        pb_reset()

    def close(self):  # -> None:
        """Close the communication."""
        return pb_close()

    def stop(self) -> None:
        """Stop the PulseBlaster program execution."""
        pb_stop()
