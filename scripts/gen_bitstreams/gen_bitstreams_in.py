#! /usr/bin/env python3

import os
import time
from distutils.dir_util import copy_tree
from queue import Empty, Queue

import progressbar
import psutil

from EcoRunnerThread import EcoRunnerThread
from PinInfoParser import PinInfoParser


class EcoRunnerThreadOut(EcoRunnerThread):
    BASE_PRJ_DIR = "../../base_projects/base_project_in"
    RESULTS_SUBDIR = "in"

    def run(self):
        STRATIXV_PIN_INFO = "../../resources/5sgsd5.txt"
        parser = PinInfoParser(STRATIXV_PIN_INFO, "F1517")
        pins = parser.get_all_pins()

        try:
            while True:
                pin_name = self.work_queue.get(block=False)
                self.log_to_file(f">>> pin_name {pin_name} <<<")

                self.set_test_pin_loc("PIN_" + pin_name)
                self.compile_fpga_project()
                self.store_results(f"{pin_name}_2V5.zip")

                self.eco('"I/O Standard"', f'"SSTL-15 Class II"')
                self.store_results(f"{pin_name}_sstl15_class2.zip")

                self.eco(
                    '"On-Chip Termination"',
                    f'"Parallel 50 Ohm with Calibration"',
                    node="|base_project|test_pin~input",
                )
                self.store_results(f"{pin_name}_sstl15_class2_term_par50.zip")

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

    return pins


def main():
    PIN_LIST_FILENAME = "../../resources/pin_list_5SGSMD5K1F40C1_8A.txt"

    pin_names = create_pin_names(PIN_LIST_FILENAME)
    work_queue = WorkQueue(pin_names)

    THREAD_COUNT = max(psutil.cpu_count(False) - 1, 1)

    threads = [EcoRunnerThreadOut(idx, work_queue) for idx in range(THREAD_COUNT)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]


if __name__ == "__main__":
    main()
