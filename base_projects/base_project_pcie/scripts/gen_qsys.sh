#! /bin/bash

set -e


# generate IPs

qsys-generate ../qsys/system_pcie.qsys \
	--block-symbol-file \
	--output-directory=../qsys/system_pcie \
	--family="Stratix V" \
	--part=5SGSMD5K2F40I3L

