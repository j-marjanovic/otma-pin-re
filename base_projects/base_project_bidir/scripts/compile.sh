#! /bin/bash

set -e


# configuration

PRJ_NAME=base_project
PRJ=../project/$PRJ_NAME


# generate IPs

qsys-generate ../ip_cores/io_tester.qsys \
    --block-symbol-file \
    --output-directory=../ip_cores/io_tester \
    --family="Stratix V" \
    --part=5SGSMD5K1F40C1

qsys-generate ../ip_cores/io_tester.qsys \
    --synthesis=VERILOG \
    --output-directory=../ip_cores/io_tester \
    --family="Stratix V" \
    --part=5SGSMD5K1F40C1


# compile bitstream

quartus_map --read_settings_files=on --write_settings_files=off $PRJ -c $PRJ_NAME
quartus_fit --read_settings_files=off --write_settings_files=off $PRJ -c $PRJ_NAME
quartus_asm --read_settings_files=off --write_settings_files=off $PRJ -c $PRJ_NAME


# check the result

file -E ../output_files/$PRJ_NAME.sof
