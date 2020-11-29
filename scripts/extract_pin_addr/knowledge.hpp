

#pragma once

/** all pin offset are based on the position of `bit_8mA` config flag - this
 * is the lowest known address for the pin */

namespace PinConfigOffsets{
  int drive_8ma = 0;
  int drive_4mA = 32;

  /** an offset for the series term on the pin output */
  int series_term = 124*8;
};
