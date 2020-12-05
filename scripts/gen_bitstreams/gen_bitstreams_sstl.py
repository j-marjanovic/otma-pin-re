#! /usr/bin/env python3

import os
import subprocess
import time
from distutils.dir_util import copy_tree
from queue import Empty, Queue
from string import Template
from threading import Thread

import progressbar

from EcoRunnerThread import EcoRunnerThread
from gen_bitstreams import EcoRunnerThread, WorkQueue, create_pin_names


class EcoRunnerThread_Sstl(EcoRunnerThread):
    BITSTREAM_SUBDIR = "sstl"

    CUR_STRENGTHS = ['"4mA"', '"6mA"', '"8mA"']

    def run(self):
        """
        We first do an ECO on "Current Strength" even if this is not needed for
        the results themselves, but it helps prevent Quartus throwing an error
        (with a very cryptic error - "Error: Inconsistant set or reset of
        compile started variable" in
        `ADB_COMMAND_STACK::set_compile_started(bool)`).

        The "Current Strength" attribute is anyway overridden later in the flow.
        """
        first_eco = True

        try:
            os.mkdir(os.path.join(self.BITSTREAM_DIR, self.BITSTREAM_SUBDIR))
        except FileExistsError:
            pass

        copy_tree(self.BASE_PRJ_DIR, self.prj_dir)
        self._compile_fpga_project()

        try:
            while True:
                pin_name = self.work_queue.get(block=False)

                if first_eco:
                    self._gen_eco('"Current Strength"', self.CUR_STRENGTHS[0])
                    self._run_eco()
                    first_eco = False

                self._gen_eco('"Location Index"', pin_name)
                self._run_eco()

                self._gen_eco('"I/O Standard"', '"SSTL-15 Class I"')
                self._run_eco()

                for cur_strength in self.CUR_STRENGTHS:
                    self._gen_eco('"Current Strength"', cur_strength)
                    self._run_eco()

                    pin_name_no_q = pin_name.replace('"', "")
                    cur_strength_no_q = cur_strength.replace('"', "")
                    dest_jic_file = os.path.join(
                        self.BITSTREAM_DIR,
                        self.BITSTREAM_SUBDIR,
                        f"sstl_{pin_name_no_q}_{cur_strength_no_q}.jic",
                    )
                    self._gen_cof(dest_jic_file)
                    self._run_cof()

        except Empty:
            self.f_log.write("> queue empty, thread exiting")
            return


def main():
    PIN_LIST_FILENAME = "../../resources/pin_list_5SGSMD5K1F40C1_full.txt"

    pin_names = create_pin_names(PIN_LIST_FILENAME)

    work_queue = WorkQueue(pin_names)

    THREAD_COUNT = 8

    threads = [EcoRunnerThread_Sstl(idx, work_queue) for idx in range(THREAD_COUNT)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]


if __name__ == "__main__":
    main()
