#! /usr/bin/env python3

import os
import time
from distutils.dir_util import copy_tree
from queue import Empty, Queue

import progressbar

from EcoRunnerThread import EcoRunnerThread


class EcoRunnerThread_2p5V(EcoRunnerThread):
    BITSTREAM_SUBDIR = "2p5V"

    CUR_STRENGTHS = ['"4mA"', '"8mA"', '"12mA"']

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

                for cur_strength in self.CUR_STRENGTHS:
                    self._gen_eco('"Current Strength"', cur_strength)
                    self._run_eco()

                    pin_name_no_q = pin_name.replace('"', "")
                    cur_strength_no_q = cur_strength.replace('"', "")
                    dest_jic_file = os.path.join(
                        self.BITSTREAM_DIR,
                        self.BITSTREAM_SUBDIR,
                        f"pin_ident_{pin_name_no_q}_{cur_strength_no_q}.jic",
                    )
                    self._gen_cof(dest_jic_file)
                    self._run_cof()

        except Empty:
            self.f_log.write("> queue empty, thread exiting")
            return


class WorkQueue(Queue):
    """ this is a little bit hackish - a queue and a progress bar combined in a single class """

    def __init__(self, pin_list):
        super().__init__()

        self.prog_bar = progressbar.ProgressBar(max_value=len(pin_list))
        self.prog_bar.start()

        for pin in pin_list:
            self.put(pin)

    def get(self, block=True, timeout=None):
        tmp = super().get(block=block, timeout=timeout)
        self.prog_bar.update(self.prog_bar.value + 1)
        return tmp


def create_pin_names(pin_list_filename):
    lines = open(pin_list_filename, "r").readlines()
    pins = [line.strip() for line in lines]
    full_pin_names = ['"PIN_{}"'.format(pin) for pin in pins]

    return full_pin_names


def main():
    # PIN_LIST_FILENAME = "../resources/pin_list_test.txt"
    PIN_LIST_FILENAME = "../../resources/pin_list_5SGSMD5K1F40C1_full.txt"

    pin_names = create_pin_names(PIN_LIST_FILENAME)

    work_queue = WorkQueue(pin_names[0:18])

    THREAD_COUNT = 6

    threads = [EcoRunnerThread_2p5V(idx, work_queue) for idx in range(THREAD_COUNT)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]


if __name__ == "__main__":
    main()
