#! /usr/bin/env python3

import csv
import logging
import re
from collections import namedtuple
from itertools import combinations
from typing import List, Dict

Pin = namedtuple("Pin", ["pin", "bank", "func", "tx_rx_ch", "dqsx8x9"])


class PinInfoParser:
    def __init__(self, filename, target_pkg):
        self.log = logging.getLogger(self.__class__.__name__)
        self.pins = dict()

        with open(filename, "r", encoding="iso-8859-1") as f:
            reader = csv.reader(f, delimiter="\t")

            # indicates that we are in the right package
            active = False

            # these indices are
            idx_bank = None
            idx_pin = None
            idx_dqsx8x9 = None
            idx_func = None

            # compare the pin name; this is used to skip comments and notes
            RE_PIN = re.compile(r"[A-Z]+\d+")

            for line in reader:
                if self.is_header(line):
                    pkg = self._get_package_from_hdr(line)
                    if pkg == target_pkg:
                        active = True
                        idx_bank = line.index("Bank Number")
                        idx_dqsx8x9 = line.index("DQS for X8/X9 ")
                        idx_func = line.index("Pin Name/Function (2)")
                        idx_pin = line.index(pkg)
                        idx_tx_rx_ch = line.index("Dedicated Tx/Rx Channel")
                    else:
                        active = False
                elif active:
                    try:
                        bank = line[idx_bank]
                        dqsx8x9 = line[idx_dqsx8x9]
                        func = line[idx_func]
                        pin = line[idx_pin]
                        tx_rx_ch = line[idx_tx_rx_ch]

                        if (
                            RE_PIN.match(pin)
                            and bank
                            and not bank[0] == "G"
                            and not func[0:4] == "VREF"
                        ):
                            self.pins[pin] = Pin(
                                pin=pin,
                                bank=bank,
                                func=func,
                                tx_rx_ch=tx_rx_ch,
                                dqsx8x9=dqsx8x9,
                            )

                        else:
                            self.log.debug("pin does not match, skipping: %s", line)
                    except Exception as e:
                        self.log.warning("unable to parse line: %s - %s", line, e)

        assert self.pins, "the parser should find plenty of pins, but none found"

    @staticmethod
    def is_header(line: List[str]) -> bool:
        """Determine if the line is a header line (different packages in one file)"""
        if not line:
            return False

        try:
            if (
                line[0] == "Bank Number"
                and line[1] == "VREF"
                and line[2] == "Pin Name/Function (2)"
            ):
                # good enough, first three match
                return True
        except IndexError:
            return False

        return False

    @staticmethod
    def _get_package_from_hdr(line: List[str]) -> str:
        """Gets package from a header line
        
        Make sure the line is a header before calling this function
        """

        return line[7]

    def get_all_pins(self) -> Dict[str, Pin]:
        return self.pins


def main():
    logging.basicConfig(level=logging.INFO)
    STRATIXV_PIN_INFO = "../../resources/5sgsd5.txt"
    parser = PinInfoParser(STRATIXV_PIN_INFO, "F1517")

    pins = parser.get_all_pins()

    for pin in pins.items():
        print(pin)


if __name__ == "__main__":
    main()
