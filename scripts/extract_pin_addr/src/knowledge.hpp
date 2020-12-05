
// Copyright (c) 2020 Jan Marjanovic

#pragma once

/** all pin offset are based on the position of `bit_8mA` config flag - this
 * is the lowest known address for the pin */

namespace PinConfigOffsets {
int drive_8ma = 0;
int drive_4mA = 32;

/** an offset for the series term on the pin output */
int series_term = 124 * 8;

std::vector<int> sstl_term = {0,   32,  64,  96,  128, 160,
                              256, 288, 320, 352, 384, 416};

std::vector<int> diff_sstl = {813536 + 1 - 813313, 813568 + 1 - 813313,
                              814112 + 1 - 813313, 814656 + 1 - 813313,
                              815488 + 1 - 813313};
}; // namespace PinConfigOffsets
