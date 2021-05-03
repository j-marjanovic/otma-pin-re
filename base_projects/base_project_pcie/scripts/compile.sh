#! /bin/bash

set -e


# configuration

PRJ_NAME=base_project_pcie
PRJ=../project/$PRJ_NAME


# compile bitstream

quartus_map --read_settings_files=on --write_settings_files=off $PRJ -c $PRJ_NAME
quartus_fit --read_settings_files=off --write_settings_files=off $PRJ -c $PRJ_NAME
quartus_asm --read_settings_files=off --write_settings_files=off $PRJ -c $PRJ_NAME


# check the result

file -E ../output_files/$PRJ_NAME.sof

