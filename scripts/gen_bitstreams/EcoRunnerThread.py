#! /usr/bin/env python3

import os
import subprocess
import time
from distutils.dir_util import copy_tree
from queue import Empty, Queue
from string import Template
from threading import Thread


class EcoRunnerThread(Thread):

    BASE_PRJ_DIR = "../../base_project"
    WORK_PRJ_DIR = "../../work/base_project"
    LOG_DIR = "../../work/log"
    SCRIPT_DIR = "../../work/script"
    BITSTREAM_DIR = "../../bitstreams/"

    def __init__(self, thread_idx: int, work_queue: Queue):
        super().__init__(name=f"eco_runner_{thread_idx}")
        self.thread_idx = thread_idx
        self.prj_dir = f"{self.WORK_PRJ_DIR}_{self.thread_idx}"
        self.work_queue = work_queue

        log_name = f"log_{self.thread_idx}_{int(time.time())}.txt"
        log_path = os.path.join(self.LOG_DIR, log_name)
        self.f_log = open(log_path, "w", buffering=1)

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
