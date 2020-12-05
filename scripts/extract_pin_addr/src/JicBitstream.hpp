
// Copyright (c) 2020 Jan Marjanovic

#pragma once

#include <fstream>
#include <iomanip>
#include <string_view>
#include <vector>

#include <boost/log/trivial.hpp>

#include "JicBitDiff.hpp"

class JicBitstream {

  std::vector<std::uint8_t> _bs;

public:
  explicit JicBitstream(std::string_view filename) { _read_file(filename); }

  std::vector<std::uint8_t> get_bytes() const { return _bs; };

  bool get_bit(int offset_bits) {
    int offset_bytes = offset_bits / 8;
    int bit_shift = offset_bits % 8;

    return (_bs[offset_bytes] >> bit_shift) & 1;
  }

  std::vector<JicBitDiff> operator^(const JicBitstream &other) {
    std::vector<std::uint8_t> diff;
    std::transform(std::begin(_bs), std::end(_bs),
                   std::begin(other.get_bytes()), std::back_inserter(diff),
                   std::bit_xor<uint8_t>());

    std::vector<JicBitDiff> non_zero_els;
    for (int addr = 0; addr < diff.size(); addr++) {
      if (diff[addr] != 0) {
        uint8_t a = _bs[addr];
        uint8_t b = other.get_bytes()[addr];
        if (_is_conf_related_change(addr)) {
          BOOST_LOG_TRIVIAL(trace)
              << "found diff at addr " << std::hex << addr
              << ", a = " << std::setw(2) << static_cast<int>(a)
              << ", b = " << std::setw(2) << static_cast<int>(b) << std::dec;
          for (int bit_addr = 0; bit_addr < 8; bit_addr++) {
            if ((diff[addr] >> bit_addr) & 1) {
              bool bit_a = (a >> bit_addr) & 1;
              bool bit_b = (b >> bit_addr) & 1;
              non_zero_els.push_back(
                  JicBitDiff{addr * 8 + bit_addr, bit_a, bit_b});
            }
          }
        } else {
          BOOST_LOG_TRIVIAL(trace)
              << "skipping diff at addr " << std::hex << addr << std::dec;
        }
      }
    }

    return non_zero_els;
  }

private:
  /** reads file into _bs */
  void _read_file(std::string_view filename) {
    BOOST_LOG_TRIVIAL(debug) << "opening " << filename;

    std::ifstream ifs{filename.data(), std::ios::binary};

    if (!ifs.good()) {
      throw std::runtime_error("could not open file");
    } else {
      BOOST_LOG_TRIVIAL(trace) << "successfully opened file";
    }

    ifs.unsetf(std::ios_base::skipws);

    ifs.seekg(0, ifs.end);
    unsigned int length = ifs.tellg();
    ifs.seekg(0, ifs.beg);

    _bs.reserve(length);
    _bs.insert(_bs.begin(), std::istream_iterator<std::uint8_t>(ifs),
               std::istream_iterator<std::uint8_t>());
    BOOST_LOG_TRIVIAL(info) << "read " << length << " bytes from " << filename;
  }

  /** uses some heuristics to detect if the change between two bitstreams is
   * related to FPGA configuration - removes changes related to the headers and
   * checksums at the end
   */
  bool _is_conf_related_change(int addr) {
    // skip header
    if (addr < 4000) {
      return false;
    }

    // skip checksum at the end
    if (addr > 33554661 - 10000) {
      return false;
    }

    return true;
  }
};
