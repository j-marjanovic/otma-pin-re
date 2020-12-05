#! /usr/bin/env python3

import os
import subprocess
import time
from distutils.dir_util import copy_tree
from queue import Empty, Queue
from string import Template
from threading import Thread

import progressbar


class EcoRunnerThread(Thread):

    BASE_PRJ_DIR = "../../base_project"
    WORK_PRJ_DIR = "../../work/base_project"
    LOG_DIR = "../../work/log"
    SCRIPT_DIR = "../../work/script"
    BITSTREAM_DIR = "../../bitstreams/"

    CUR_STRENGTHS = ['"4mA"', '"8mA"', '"12mA"']

    def __init__(self, thread_idx: int, work_queue: Queue):
        super().__init__(name=f"eco_runner_{thread_idx}")
        self.thread_idx = thread_idx
        self.prj_dir = f"{self.WORK_PRJ_DIR}_{self.thread_idx}"
        self.work_queue = work_queue

        log_name = f"log_{self.thread_idx}_{int(time.time())}.txt"
        log_path = os.path.join(self.LOG_DIR, log_name)
        self.f_log = open(log_path, "w", buffering=1)

    def run(self):
        copy_tree(self.BASE_PRJ_DIR, self.prj_dir)
        self._compile_fpga_project()

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
                        BITSTREAM_DIR,
                        f"pin_ident_{pin_name_no_q}_{cur_strength_no_q}.jic",
                    )
                    self._gen_cof(dest_jic_file)
                    self._run_cof()

        except Empty:
            self.f_log.write("> queue empty, thread exiting")
            return

    def _compile_fpga_project(self):
        """ Compile FPGA project """
        subprocess.call(
            ["./compile.sh"],
            cwd=os.path.join(self.prj_dir, "scripts"),
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            stdout=self.f_log,
        )

    def _gen_eco(self, info_type, value):
        """Generate eco.tcl file to be used with quartus_cdb

        Args:
            info_type: e.g. "Current Strength" or "Location Index", should be already quoted
            value: e.g. "4mA" or "PIN_A6", should be already quoted
        """

        self.f_log.write("> gen_eco\n")

        quartus_prj_dir = os.path.join(self.prj_dir, "project", "base_project")

        eco_tcl_temp = Template(open("eco.tcl.template", "r").read())
        eco_tcl_str = eco_tcl_temp.substitute(
            templ_quartus_prj_dir=quartus_prj_dir,
            templ_into_type=info_type,
            templ_value=value,
        )

        open(self._get_eco_filename(), "w").write(eco_tcl_str)

    def _run_eco(self):
        """ Performs ECO changes (in eco.tcl) and recompiles the design """

        self.f_log.write("> run_eco\n")

        subprocess.call(
            ["quartus_cdb", "-t", self._get_eco_filename()],
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            stdout=self.f_log,
        )

    def _gen_cof(self, output_filename):
        """Generate .cof file to be used with `quartus_cpf`  """

        self.f_log.write("> gen_cof\n")

        quartus_out_dir = os.path.join(self.prj_dir, "output_files")

        conv_to_jic_temp = Template(open("conv_to_jic.cof.template", "r").read())
        conv_to_jic_str = conv_to_jic_temp.substitute(
            templ_quartus_out_dir=quartus_out_dir, templ_output_filename=output_filename
        )

        open(self._get_cof_filename(), "w").write(conv_to_jic_str)

    def _run_cof(self):
        """ Run `quartus_cpf` """

        self.f_log.write("> run_cof\n")

        subprocess.call(
            ["quartus_cpf", "-c", self._get_cof_filename()],
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            stdout=self.f_log,
        )

    def _get_eco_filename(self):
        return os.path.join(self.SCRIPT_DIR, f"eco_{self.thread_idx}.tcl")

    def _get_cof_filename(self):
        return os.path.join(self.SCRIPT_DIR, f"conv_to_jic_{self.thread_idx}.cof")


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
    PIN_LIST_FILENAME = "../resources/pin_list_5SGSMD5K1F40C1_full.txt"

    pin_names = create_pin_names(PIN_LIST_FILENAME)

    work_queue = WorkQueue(pin_names)

    THREAD_COUNT = os.cpu_count() - 2

    threads = [EcoRunnerThread(idx, work_queue) for idx in range(THREAD_COUNT)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]


if __name__ == "__main__":
    main()
