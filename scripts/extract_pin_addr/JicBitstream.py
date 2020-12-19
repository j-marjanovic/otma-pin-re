import os
import zipfile

import numpy as np


class JicBitstream:
    def __init__(self, jic_filename):
        jic = open(jic_filename, "rb").read()
        jic = np.frombuffer(jic, dtype=np.uint8)
        jic = np.unpackbits(jic)
        self.jic = jic

    def diff_pos(self, other):
        diff = self.jic ^ other.jic
        nz_els = np.nonzero(diff)
        return nz_els

    def get_els(self, addrs):
        return self.jic[addrs]


class JicBitstreamZip(JicBitstream):
    def __init__(self, zip_filename):
        with zipfile.ZipFile(zip_filename, mode="r") as zip:
            jic = zip.open("base_project.jic", "r").read()
            jic = np.frombuffer(jic, dtype=np.uint8)
            jic = np.unpackbits(jic)
            self.jic = jic
