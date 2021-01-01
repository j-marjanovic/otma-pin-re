import os
import zipfile

import numpy as np


class JicBitstream:
    def __init__(self, jic_filename):
        jic = open(jic_filename, "rb").read()
        jic = np.frombuffer(jic, dtype=np.uint8)
        self.jic_uint8 = jic
        jic = np.unpackbits(jic)
        self.jic = jic

    def diff_pos(self, other):
        diff = self.jic ^ other.jic
        nz_els = np.nonzero(diff)
        return nz_els

    def get_els(self, addrs):
        return self.jic[addrs]

    def find_jjjj_seqs(self):
        JJJJ = np.array([ord('j')]*4, dtype=np.uint8)

        possible_locs = np.where(self.jic_uint8 == ord('j'))[0]
        found_locs = []

        for loc in possible_locs:
            if np.all(self.jic_uint8[loc:loc+4] == JJJJ):
                found_locs.append(loc)

        return found_locs

class JicBitstreamZip(JicBitstream):
    def __init__(self, zip_filename):
        with zipfile.ZipFile(zip_filename, mode="r") as zip:
            jic = zip.open("base_project.jic", "r").read()
            jic = np.frombuffer(jic, dtype=np.uint8)
            self.jic_uint8 = jic
            jic = np.unpackbits(jic)
            self.jic = jic
