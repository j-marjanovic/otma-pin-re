#! /usr/bin/env python3

import os
import subprocess
import time
import zipfile
from distutils.dir_util import copy_tree
from queue import Empty, Queue
from string import Template
from threading import Thread


class EcoRunnerThread(Thread):

    BASE_PRJ_DIR = None
    RESULTS_SUBDIR = None
    WORK_PRJ_DIR = "../../work/base_project"
    LOG_DIR = "../../work/log"
    SCRIPT_DIR = "../../work/script"
    RESULTS_DIR = "../../results/"

    def __init__(self, thread_idx: int, work_queue: Queue):
        super().__init__(name=f"eco_runner_{thread_idx}")

        if self.BASE_PRJ_DIR is None or self.RESULTS_SUBDIR is None:
            raise ValueError(
                "BASE_PRJ_DIR and RESULTS_SUBDIR should be defined in parent class"
            )

        self.thread_idx = thread_idx
        self.work_queue = work_queue

        # prepare paths
        self.prj_dir = f"{self.WORK_PRJ_DIR}_{self.thread_idx}"
        self.output_filename_full = os.path.join(
            self.prj_dir, "output_files", "base_project.jic"
        )

        # create a folder for the results
        if thread_idx == 0:
            os.mkdir(os.path.join(self.RESULTS_DIR, self.RESULTS_SUBDIR))

        # prepare base project
        copy_tree(self.BASE_PRJ_DIR, self.prj_dir)

        # prepare (file-based) logging
        log_name = f"log_{self.thread_idx}_{int(time.time())}.txt"
        log_path = os.path.join(self.LOG_DIR, log_name)
        self.f_log = open(log_path, "w", buffering=1)

    def _gen_eco(self, info_type, value, node):
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
            templ_node=node
        )

        open(self._get_eco_filename(), "w").write(eco_tcl_str)

    def _run_eco(self):
        """ Performs ECO changes (in eco.tcl) and recompiles the design """

        self.f_log.write("> run_eco\n")

        rc = subprocess.call(
            ["quartus_cdb", "-t", self._get_eco_filename()],
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            stdout=self.f_log,
        )

        if rc != 0:
            self.f_log.write(f"> run_eco failed with rc = {rc}\n")
            raise RuntimeError("Running ECO failed")

    def _gen_cof(self):
        """Generate .cof file to be used with `quartus_cpf`  """

        self.f_log.write("> gen_cof\n")

        quartus_out_dir = os.path.join(self.prj_dir, "output_files")

        conv_to_jic_temp = Template(open("conv_to_jic.cof.template", "r").read())
        conv_to_jic_str = conv_to_jic_temp.substitute(
            templ_quartus_out_dir=quartus_out_dir,
            templ_output_filename=self.output_filename_full,
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

    def compile_fpga_project(self):
        """ Compile FPGA project """

        rc = subprocess.call(
            ["./compile.sh"],
            cwd=os.path.join(self.prj_dir, "scripts"),
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            stdout=self.f_log,
        )

        if rc != 0:
            self.f_log.write(f"> compile_fpga_project failed with rc = {rc}\n")
            raise RuntimeError("Compilation failed")

    def eco(self, info_type, value, node="|base_project|test_pin"):
        self.f_log.write(f"> eco {info_type} {value}\n")

        self._gen_eco(info_type, value, node)
        self._run_eco()

    def _modify_qsf_file(self, func, append_lines=None):
        qsf_filename = os.path.join(self.prj_dir, "project/base_project.qsf")
        with open(qsf_filename) as f_in:
            lines = f_in.readlines()

        with open(qsf_filename, "w") as f_out:
            for line in lines:
                func(line, f_out)

            if append_lines is not None:
                f_out.write("\n")
                for line in append_lines:
                    f_out.write(line + "\n")

    def set_test_pin_io_std(self, io_std):
        self.f_log.write(f"> set_test_pin_io_std {io_std}\n")

        def f(line, f_out):
            if (
                line.find("set_instance_assignment -name IO_STANDARD") == 0
                and line.find("-to test_pin") > 0
            ):
                f_out.write(
                    f'set_instance_assignment -name IO_STANDARD "{io_std}" -to test_pin\n'
                )
            else:
                f_out.write(line)

        self._modify_qsf_file(f, None)

    def set_test_pin_loc(self, loc):
        self.f_log.write(f"> set_test_pin_loc {loc}\n")

        def f(line, f_out):
            if (
                line.find("set_location_assignment") == 0
                and line.find("-to test_pin") > 0
            ):
                f_out.write(f"set_location_assignment {loc} -to test_pin\n")
            else:
                f_out.write(line)

        self._modify_qsf_file(f, None)

    def set_output_term_off(self):
        self.f_log.write(f"> set_output_term_off\n")

        def f(line, f_out):
            f_out.write(line)

        append_lines = [
            'set_instance_assignment -name OUTPUT_TERMINATION OFF -to "test_pin(n)"',
            'set_instance_assignment -name OUTPUT_TERMINATION OFF -to test_pin',
        ]

        self.set_output_term_default()
        self._modify_qsf_file(f, append_lines)

    def set_output_term_default(self):
        self.f_log.write(f"> set_output_term_default\n")

        def f(line, f_out):
            if (
                line.find("set_instance_assignment -name OUTPUT_TERMINATION") == 0
                and line.find("test_pin") > 0
            ):
                pass
            else:
                f_out.write(line)

        self._modify_qsf_file(f, None)

    def set_cur_strength(self, cur):
        self.f_log.write(f"> set_cur_strength {cur}\n")

        def f(line, f_out):
            f_out.write(line)

        append_lines = [
            f"set_instance_assignment -name CURRENT_STRENGTH_NEW {cur.upper()} -to test_pin",
            f'set_instance_assignment -name CURRENT_STRENGTH_NEW {cur.upper()} -to "test_pin(n)"',
        ]

        self.set_cur_strength_default()
        self._modify_qsf_file(f, append_lines)

    def set_cur_strength_default(self):
        self.f_log.write(f"> set_cur_strength_default\n")
        def f(line, f_out):
            if (
                line.find("set_instance_assignment -name CURRENT_STRENGTH_NEW") == 0
                and line.find("test_pin") > 0
            ):
                pass
            else:
                f_out.write(line)

        self._modify_qsf_file(f, None)

    def store_results(self, out_file):
        self.f_log.write(f"> store results: {out_file}\n")

        self._gen_cof()
        self._run_cof()

        out_file_full = os.path.join(self.RESULTS_DIR, self.RESULTS_SUBDIR, out_file)

        stat = os.stat(self.output_filename_full)
        self.f_log.write(f"stat {out_file}: {stat}")

        with zipfile.ZipFile(
            out_file_full, mode="w", compression=zipfile.ZIP_LZMA
        ) as zp:
            basename = os.path.basename(self.output_filename_full)

            jic_bytes = open(self.output_filename_full, "rb").read()
            with zp.open(basename, "w") as jic:
                jic.write(jic_bytes)

            pin_filename = os.path.join(
                self.prj_dir, "output_files", "base_project.pin"
            )
            pin_bytes = open(pin_filename, "rb").read()
            with zp.open("pin.txt", "w") as pin:
                pin.write(pin_bytes)

            rpt_filename = os.path.join(
                self.prj_dir, "output_files", "base_project.fit.rpt"
            )
            rpt_bytes = open(rpt_filename, "rb").read()
            with zp.open("fit_report.txt", "w") as rpt:
                rpt.write(rpt_bytes)
