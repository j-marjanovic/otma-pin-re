#! /usr/bin/env python3

import subprocess
import time
from string import Template

import progressbar


PIN_LIST_FILENAME = "../resources/pin_list_test.txt"
PIN_LIST_FILENAME = "../resources/pin_list_5SGSMD5K1F40C1_full.txt"

f = open(f"log_{int(time.time())}.txt", "w", buffering=1)


def create_pin_names():
    lines = open(PIN_LIST_FILENAME, "r").readlines()
    pins = [line.strip() for line in lines]
    full_pin_names = ['"PIN_{}"'.format(pin) for pin in pins]

    return full_pin_names


def compile_fpga_project():
    subprocess.call(
        ["./compile.sh"],
        cwd="../base_project/scripts",
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        stdout=f,
    )


def gen_eco(info_type, value):
    """Generate eco.tcl file to be used with quartus_cdb

    Args:
        info_type: e.g. "Current Strength" or "Location Index", should be already quoted
        value: e.g. "4mA" or "PIN_A6", should be already quoted
    """

    eco_tcl_temp = Template(open("eco.tcl.template", "r").read())
    eco_tcl_str = eco_tcl_temp.substitute(templ_into_type=info_type, templ_value=value)
    open("eco.tcl", "w").write(eco_tcl_str)


def run_eco():
    """ Performs ECO changes (in eco.tcl) and recompiles the design """

    subprocess.call(
        ["quartus_cdb", "-t", "eco.tcl"],
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        stdout=f,
    )


def gen_cof(output_filename):
    """Generate .cof file to be used with `quartus_cpf`  """

    conv_to_jic_temp = Template(open("conv_to_jic.cof.template", "r").read())
    conv_to_jic_str = conv_to_jic_temp.substitute(templ_output_filename=output_filename)
    open("conv_to_jic.cof", "w").write(conv_to_jic_str)


def run_cof():

    subprocess.call(
        ["quartus_cpf", "-c", "conv_to_jic.cof"],
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        stdout=f,
    )


def main():
    pin_names = create_pin_names()
    cur_strengths = ['"4mA"', '"8mA"', '"12mA"']

    tot_iter = 1 + len(pin_names) * len(cur_strengths)
    bar = progressbar.ProgressBar(max_value=tot_iter)
    bar.start()

    compile_fpga_project()
    bar.update(bar.value + 1)

    for pin_name in pin_names:
        gen_eco('"Location Index"', pin_name)
        run_eco()

        for cur_strength in cur_strengths:
            gen_eco('"Current Strength"', cur_strength)
            run_eco()
            pin_name_no_q = pin_name.replace('"', "")
            cur_strength_no_q = cur_strength.replace('"', "")
            gen_cof(f"../bitstreams/pin_ident_{pin_name_no_q}_{cur_strength_no_q}.jic")
            run_cof()
            bar.update(bar.value + 1)


if __name__ == "__main__":
    main()
