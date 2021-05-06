#! /usr/bin/env python3

import copy
import dataclasses
import os
import xml.etree.ElementTree
from queue import Empty, Queue
from threading import Lock
from typing import List

import progressbar
import psutil

from EcoRunnerThread import EcoRunnerThread


@dataclasses.dataclass
class PcieConfig:
    vendor_id: int = 0
    device_id: int = 0
    class_code: int = 0
    subsystem_device_id: int = 0
    subsystem_vendor_id: int = 0
    bar0_type: int = 2
    bar0_size_mask: int = 10
    bar2_type: int = 0
    bar2_size_mask: int = 0

    @staticmethod
    def abbreviate(s: str) -> str:
        arr = s.split("_")

        tmp = ""
        for el in arr:
            tmp += el[0]
            for c in el:
                if c.isdigit():
                    tmp += c

        return tmp

    def get_compact_str(self) -> str:
        keys = dataclasses.asdict(self).keys()
        vals = dataclasses.asdict(self).values()

        k_str = "".join([self.abbreviate(key) for key in keys])
        v_str = "_".join([str(val) for val in vals])

        return k_str + "-" + v_str


class EcoRunnerThreadPcie(EcoRunnerThread):
    BASE_PRJ_DIR = "../../base_projects/base_project_pcie"
    RESULTS_SUBDIR = "pcie"

    def _get_qsys_pcie_filename(self):
        return os.path.join(self.prj_dir, "qsys", "system_pcie.qsys")

    def _modify_qsys_pcie(self, pcie_config):
        """Update qsys elements"""

        self.f_log.write("> _modify_qsys_pcie\n")
        qsys_path = self._get_qsys_pcie_filename()
        self.f_log.write(f">     {qsys_path}\n")

        et = xml.etree.ElementTree.parse(qsys_path)

        r = et.getroot()
        mods = r.findall("module")
        assert len(mods) == 1
        m = mods[0]

        for k, v in dataclasses.asdict(pcie_config).items():
            els = m.findall(f".//*[@name='{k}_hwtcl']")
            assert len(els) == 1

            el = els[0]
            el.set("value", str(v))

        et.write(qsys_path)

    def run(self):
        try:
            while True:
                conf = self.work_queue.get(block=False)

                self.log_to_file(f">>> conf {conf} <<<")

                self._modify_qsys_pcie(conf)
                self.gen_qsys()
                self.compile_fpga_project()
                self.store_results(f"pcie_{conf.get_compact_str()}.zip")

        except Empty:
            self.f_log.write("> queue empty, thread exiting")
            return


class WorkQueue(Queue):
    """this is a little bit hackish - a queue and a progress bar combined in a single class"""

    def __init__(self, pin_list):
        super().__init__()

        self.lock = Lock()

        self.prog_bar = progressbar.ProgressBar(max_value=len(pin_list))
        self.prog_bar.start()

        for pin in pin_list:
            self.put(pin)

    def get(self, block=True, timeout=None):
        tmp = super().get(block=block, timeout=timeout)
        with self.lock:
            self.prog_bar.update(self.prog_bar.value + 1)
        return tmp


def create_all_configs() -> List[PcieConfig]:
    """
    vendor_id_hwtcl = [0, 1, 2]
    device_id_hwtcl = [0, 11, 22]
    class_code_hwtcl = [0, 31, 62]
    subsystem_device_id_hwtcl = [0, 17]
    subsystem_vendor_id_hwtcl = [0, 13]
    bar0_type_hwtcl = [0, 2]
    bar0_size_mask_hwtcl = [0, 20, 28]
    bar2_type_hwtcl = [0, 2]
    bar2_size_mask_hwtcl = [0, 15, 20]
    """

    base_conf = PcieConfig()

    all_combs: List[PcieConfig] = [base_conf]

    for vendor_id in [1, 2, 0xFFFE]:
        c = copy.copy(base_conf)
        c.vendor_id = vendor_id
        all_combs.append(c)

    """
    for device_id in [1, 2, 0xFFFE]:
        c = copy.copy(base_conf)
        c.device_id = device_id
        all_combs.append(c)

    for class_code in [1, 2, 0xFFFE]:
        c = copy.copy(base_conf)
        c.class_code = class_code
        all_combs.append(c)
    """

    for c in all_combs:
        print(c)

    print(len(all_combs))

    return all_combs


def main():

    configs = create_all_configs()
    print(configs)

    work_queue = WorkQueue(configs)

    THREAD_COUNT = 2  # max(psutil.cpu_count(False) - 1, 1)

    threads = [EcoRunnerThreadPcie(idx, work_queue) for idx in range(THREAD_COUNT)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]


if __name__ == "__main__":
    main()
