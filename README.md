# Stratix V pin configuration RE

This project aims to reverse engineer the pin configuration (e.g. IO standard,
direction, pull-up and termination resistors, ...) in a bitstream for Stratix
V.

Compared to other FPGA reverse-engineering efforts this project has a very
limited scope. The objective is to understand enough of the bitstream
organization to be able to extract the DDR3 pin out on the Pikes Peak board
(https://j-marjanovic.io/stratix-v-accelerator-card-from-ebay.html).

## The final result

The final result of this RE effort is available in
[scripts/extract_pin_addr/07_application.ipynb] as a list of pins, annotated
with their function as a part of the DDR3 interace.
