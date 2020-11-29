
#include <algorithm>
#include <bit>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <vector>

#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "knowledge.hpp"
#include "utils.hpp"

int get_val(const std::vector<std::uint8_t> &bs_a, int offset_bits) {

  int offset_bytes = offset_bits / 8;
  int bit_shift = offset_bits % 8;

  return (bs_a[offset_bytes] >> bit_shift) & 1;
}

int main() {

  namespace pt = boost::property_tree;
  pt::ptree root;
  pt::read_json("../../artifacts/pin_summary.json", root);

  int tot = 0;
  int scanned = 0;

  std::vector<std::uint8_t> bs =
      read_file("../../bitstream_ref/factory_trim2.jic");

  for (auto &it : root) {
    int base_addr = it.second.get<int>("bit_8mA");
    // int addr = ;
    int val = get_val(bs, base_addr + PinConfigOffsets::series_term);
    int val2 = get_val(bs, base_addr + 64);

    if (val) {
      tot++;
    }
    scanned++;

    if (val) {
      std::cout << it.first << ", val = " << val << ", " << val2 << ", tot = " << tot
                << ", prog = " << scanned << "\n";
    }
  }
}
