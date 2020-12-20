#! /bin/bash

set -e


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
