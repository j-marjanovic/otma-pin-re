import pickle
import sys
from collections import namedtuple

import numpy as np

from JicBitstream import JicBitstream
from knowledge import PU_ADDR
from knowledge2 import BLK_LOC_START_BIT, UNKNW_BLK_LOWER_LIM, UNKWN_BLK_NR

sys.path.append("../gen_bitstreams")
from PinInfoParser import PinInfoParser

IOSTD_REL_TO_PU = np.array(
    [
        -1056,
        -512,
        -480,
        -448,
        -416,
        -384,
        -352,
        -320,
        -288,
        -256,
        -224,
        -192,
        -160,
        -128,
        -96,
        -64,
        -32,
        0,
        256,
        288,
        512,
        544,
        864,
        1504,
        1536,
        1600,
        1664,
        1696,
    ]
)

IOclassifierOut = namedtuple(
    "IOclassifierOut", ["inp", "out", "pu", "io_std", "term", "diff"]
)


class IOclassifier:
    IDX_PU = 0
    IDX_INPUT_ACT_B = 288
    IDX_INPUT_ACT_B_DIFF = -1056

    # output will have at least one of those set, input will have all zeros
    IDX_OUTPUT = [-512, -480, -416, -384, -320, -288, -256, -224, -192, -160, -128, 544]

    # [0, 0, 1] = def, [1, 1 0] = class 1 or 2
    IDX_SSTL_TERM = [-256, -224, 544]

    IDX_OUT_DT = pickle.load(open("IDX_OUT_DT.p", "rb"))
    dtree_out = pickle.load(open("out_std_dtc.p", "rb"))

    STRATIXV_PIN_INFO = "../../resources/5sgsd5.txt"
    parser = PinInfoParser(STRATIXV_PIN_INFO, "F1517")
    pins_info = parser.get_all_pins()
    IDX_IO_STD_RX_DIFF = 1664
    IDX_IO_STD_TX_DIFF = 1696

    idx_vec = IOSTD_REL_TO_PU

    @staticmethod
    def _offs_cor(addr, pin):
        addr -= np.sum(addr > BLK_LOC_START_BIT) * 64
        unknw_blk_lower_lim = UNKNW_BLK_LOWER_LIM[pin]
        unknw_blk_nr = UNKWN_BLK_NR[pin]

        if addr > unknw_blk_lower_lim:
            addr -= unknw_blk_nr * 1344

        return addr

    @staticmethod
    def _offs_cor_reverse(addr, pin):
        unknw_blk_lower_lim = UNKNW_BLK_LOWER_LIM[pin]
        unknw_blk_nr = UNKWN_BLK_NR[pin]

        if addr > unknw_blk_lower_lim:
            addr += unknw_blk_nr * 1344

        est_addr = addr + (np.sum(addr > BLK_LOC_START_BIT) * 64)
        est_addr = addr + (np.sum(est_addr > BLK_LOC_START_BIT) * 64)
        addr += np.sum(est_addr > BLK_LOC_START_BIT) * 64

        return addr

    @staticmethod
    def get_indices(arr, vals):
        idxs = []
        for val in vals:
            idxs.append(np.where(arr == val)[0][0])
        return np.array(idxs)

    def __init__(self):
        pass

    def classify(self, jic: JicBitstream, pin_lst):
        return [self._classify_pin(jic, pin) for pin in pin_lst]

    def _classify_pin(self, jic, pin):
        feat_addrs = IOSTD_REL_TO_PU + self._offs_cor(PU_ADDR[pin], pin)
        feat_addrs = np.array(
            [self._offs_cor_reverse(addr, pin) for addr in feat_addrs]
        )
        feat = jic.get_els(feat_addrs).astype(int)
        has_pu = self._has_pull_up(feat)
        has_output = self._has_output(feat)
        diff = self._has_diff(feat, pin)
        has_input = self._has_input(feat, diff)
        io_std = self._get_iostd(feat)

        if io_std[0][0] == "S":
            sstl_term = self._get_sstl_term(feat)
        else:
            sstl_term = None

        return IOclassifierOut(
            inp=has_input,
            out=has_output,
            pu=has_pu,
            io_std=io_std[0],
            term=sstl_term,
            diff=diff,
        )

    def _has_pull_up(self, feat):
        pu_idx = np.where(self.idx_vec == self.IDX_PU)[0][0]
        return bool(feat[pu_idx])

    def _has_output(self, feat):
        out_idxs = self.get_indices(self.idx_vec, self.IDX_OUTPUT)
        return np.any(feat[out_idxs])

    def _has_input(self, feat, diff):
        if diff:
            in_idx = np.where(self.idx_vec == self.IDX_INPUT_ACT_B_DIFF)[0][0]
        else:
            in_idx = np.where(self.idx_vec == self.IDX_INPUT_ACT_B)[0][0]
        feat_input = feat[in_idx]
        return not bool(feat_input)

    def _get_iostd(self, feat):
        idxs_iostd = self.get_indices(self.idx_vec, self.IDX_OUT_DT)
        feat_iostd = feat[idxs_iostd]
        return self.dtree_out.predict(feat_iostd.reshape(1, -1))[0]

    def _get_sstl_term(self, feat):
        idxs_sstl_term = self.get_indices(self.idx_vec, self.IDX_SSTL_TERM)
        feat_sstl_term = feat[idxs_sstl_term]
        DEF_TERM = np.array([0, 0, 1])
        CL1_2_TERM = np.array([1, 1, 0])

        # pylint: disable=no-else-return
        if np.array_equal(feat_sstl_term, DEF_TERM):
            return "SSTL, term"
        elif np.array_equal(feat_sstl_term, CL1_2_TERM):
            return "SSTL cl1/2, term"
        else:
            return "no term"

    def _has_diff(self, feat, pin):
        if self.pins_info[pin].tx_rx_ch.find("DIFFIO_RX") == 0:
            diff_idx = np.where(self.idx_vec == self.IDX_IO_STD_RX_DIFF)[0][0]
        else:
            diff_idx = np.where(self.idx_vec == self.IDX_IO_STD_TX_DIFF)[0][0]

        feat_diff = feat[diff_idx]
        return bool(feat_diff)
