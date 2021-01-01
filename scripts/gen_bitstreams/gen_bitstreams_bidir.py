#! /usr/bin/env python3

import os
import time
from distutils.dir_util import copy_tree
from queue import Empty, Queue

import progressbar
import psutil

from EcoRunnerThread import EcoRunnerThread
from PinInfoParser import PinInfoParser


class EcoRunnerThreadBidir(EcoRunnerThread):
    BASE_PRJ_DIR = "../../base_projects/base_project_bidir"
    RESULTS_SUBDIR = "bidir_bank3c"

    def run(self):
        STRATIXV_PIN_INFO = "../../resources/5sgsd5.txt"
        parser = PinInfoParser(STRATIXV_PIN_INFO, "F1517")
        pins = parser.get_all_pins()

        self.gen_qsys()

        try:
            while True:
                pin_name = self.work_queue.get(block=False)
                self.log_to_file(f">>> pin_name {pin_name} <<<")

                self.set_test_pin_loc("PIN_" + pin_name)
                self.set_test_pin_io_std("2.5 V")
                self.compile_fpga_project()
                self.store_results(f"{pin_name}_2V5_on_chip_term.zip")

                self.eco(
                    '"On-Chip Termination"',
                    f'"Off"',
                    node="|base_project|test_pin~output",
                )
                self.store_results(f"{pin_name}_2V5_on_chip_term_off.zip")

                for pu in ["on", "off"]:
                    self.eco('"Weak Pull Up"', f'"{pu}"')

                    for cur in ["4mA", "8mA", "12mA", "16mA"]:
                        self.eco('"Current Strength"', f'"{cur}"')
                        self.store_results(f"{pin_name}_2V5_{cur}_pu_{pu}_dly_no.zip")

                self.eco('"Weak Pull Up"', f'"off"')
                self.eco('"Current Strength"', '"4mA"')

                """
                for dly in ["1", "2", "0"]:
                    self.eco('"D5 Delay Chain"', f'"{dly}"')
                    self.store_results(f"{pin_name}_2V5_4mA_pu_off_dly_{dly}.zip")
                """

                self.set_test_pin_io_std("SSTL-15")
                self.set_cur_strength_default()
                self.compile_fpga_project()
                self.store_results(f"{pin_name}_sstl15_default.zip")

                self.set_test_pin_io_std("SSTL-15 CLASS I")
                self.compile_fpga_project()
                self.store_results(f"{pin_name}_sstl15_class1_default.zip")

                self.eco(
                    '"On-Chip Termination"',
                    f'"Off"',
                    node="|base_project|test_pin~output",
                )
                for cur in ["4mA", "6mA", "8mA", "10mA", "12mA"]:
                    self.eco('"Current Strength"', f'"{cur}"')
                    self.store_results(f"{pin_name}_sstl15_class1_term_off_{cur}.zip")

                self.set_test_pin_io_std("SSTL-15 CLASS II")
                self.compile_fpga_project()
                self.store_results(f"{pin_name}_sstl15_class2_default.zip")

                self.eco(
                    '"On-Chip Termination"',
                    f'"Off"',
                    node="|base_project|test_pin~output",
                )
                for cur in ["8mA", "16mA"]:
                    self.eco('"Current Strength"', f'"{cur}"')
                    self.store_results(f"{pin_name}_sstl15_class2_term_off_{cur}.zip")

                # disable the entire diff compilation
                if (
                    False
                    and pins[pin_name].tx_rx_ch[-1] == "p"
                    and not (pins[pin_name].tx_rx_ch.find("DIFFIO_TX") == 0)
                ):
                    # 1
                    """
                    if pins[pin_name].tx_rx_ch.find("DIFFIO_TX") == 0:
                        self.set_test_pin_io_std("LVDS")
                        self.compile_fpga_project()
                        self.store_results(f"{pin_name}_lvds.zip")
                    else:
                        self.log_to_file(f"skipping LVDS for pin {pin_name}")
                    """

                    # 2
                    self.set_test_pin_io_std("DIFFERENTIAL 1.5-V SSTL")
                    self.compile_fpga_project()
                    self.store_results(f"{pin_name}_diff_sstl15_default.zip")

                    # 3
                    self.set_test_pin_io_std("DIFFERENTIAL 1.5-V SSTL CLASS I")
                    self.compile_fpga_project()
                    self.store_results(f"{pin_name}_diff_sstl15_class1_default.zip")

                    # 3b
                    self.set_output_term_off()

                    for cur in ["4mA", "6mA", "8mA", "10mA", "12mA"]:
                        self.set_cur_strength(cur)
                        self.compile_fpga_project()
                        self.store_results(
                            f"{pin_name}_diff_sstl15_class1_term_off_{cur}.zip"
                        )

                    self.set_output_term_default()
                    self.set_cur_strength_default()

                    # 4
                    self.set_test_pin_io_std("DIFFERENTIAL 1.5-V SSTL CLASS II")
                    self.compile_fpga_project()
                    self.store_results(f"{pin_name}_diff_sstl15_class2_default.zip")

                    # 4b
                    self.set_output_term_off()

                    for cur in ["8mA", "16mA"]:
                        self.set_cur_strength(cur)
                        self.compile_fpga_project()
                        self.store_results(
                            f"{pin_name}_diff_sstl15_class2_term_off_{cur}.zip"
                        )

                    self.set_output_term_default()
                    self.set_cur_strength_default()
                else:
                    self.log_to_file(f"skipping diff for pin {pin_name}")

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
    PIN_LIST_FILENAME = "../../resources/pin_list_5SGSMD5K1F40C1_3C.txt"

    pin_names = create_pin_names(PIN_LIST_FILENAME)
    work_queue = WorkQueue(pin_names)

    THREAD_COUNT = max(psutil.cpu_count(False) - 1, 1)

    threads = [EcoRunnerThreadBidir(idx, work_queue) for idx in range(THREAD_COUNT)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]


if __name__ == "__main__":
    main()
