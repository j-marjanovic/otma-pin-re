
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

/** read file into a vector of bytes */
std::vector<std::uint8_t> read_file(const std::string &filename) {

  std::ifstream ifs{filename, std::ios::binary};

  if (!ifs.good()) {
    std::cout << "error opening file, exiting\n";
    throw std::runtime_error("could not open file");
  }

  ifs.unsetf(std::ios_base::skipws);

  ifs.seekg(0, ifs.end);
  unsigned int length = ifs.tellg();
  ifs.seekg(0, ifs.beg);

  std::vector<std::uint8_t> bs;
  bs.reserve(length);
  bs.insert(bs.begin(), std::istream_iterator<std::uint8_t>(ifs),
            std::istream_iterator<std::uint8_t>());

  return bs;
}

/** uses some heuristics to detect if the change between two bitstreams
 * is related to FPGA pin configuration
 */
bool is_pin_related_change(int addr, uint8_t a, uint8_t b) {
  if (addr < 4096) {
    return false;
  }

  if (addr > 33554659 - 4096) {
    return false;
  }

  uint8_t x = a ^ b;
  if (__builtin_popcount(x) > 1) {
    return false;
  }

  return true;
}

/** gets the log2 of the lowest bit set, throws exception if none found */
int log2single(uint8_t x) {
  for (int i = 0; i < 8; i++) {
    if ((x >> i) & 1) {
      return i;
    }
  }

  throw std::runtime_error("no set bits found");
}

/** hold information about the differences between the two bitstreams */
struct BitDiff {
  int addr;
  uint8_t a, b;
};

std::ostream &operator<<(std::ostream &os, const BitDiff &bd) {
  os << "BitDiff{addr = " << bd.addr << ", a = 0x" << std::hex
     << static_cast<int>(bd.a) << ", b = 0x" << static_cast<int>(bd.b)
     << std::dec << "}";
  return os;
}

/** gets the first position related to pin change (in bit address) between two
 * bitstreams
 */
int get_first_pos(std::string &filename_a, std::string &filename_b) {
  std::vector<std::uint8_t> bs_a = read_file(filename_a);
  std::vector<std::uint8_t> bs_b = read_file(filename_b);

  std::vector<std::uint8_t> diff;

  std::transform(std::begin(bs_a), std::end(bs_a), std::begin(bs_b),
                 std::back_inserter(diff), std::bit_xor<uint8_t>());

  std::vector<BitDiff> non_zero_els;
  for (int i = 0; i < diff.size(); i++) {
    if (diff[i] != 0) {
      if (is_pin_related_change(i, bs_a[i], bs_b[i])) {
        non_zero_els.push_back(BitDiff{i, bs_a[i], bs_b[i]});
        // std::cout << i << ", " << static_cast<int>(bs_a[i]) << ", " <<
        // static_cast<int>(bs_b[i]) << "\n";
      }
    }
  }

  int bit_addr = non_zero_els[0].addr * 8 +
                 log2single(non_zero_els[0].a ^ non_zero_els[0].b);
  return bit_addr;
}

int main() {

  std::ifstream infile{"../../resources/pin_list_5SGSMD5K1F40C1_full.txt"};
  std::string line;

  namespace pt = boost::property_tree;
  pt::ptree root;

  std::string bitstream_path = "../../bitstreams/pin_ident_PIN_";

  while (infile >> line) {
    std::cout << "line = " << line << "\n";
    std::string filename_4mA{bitstream_path + line + "_4mA.jic"};
    std::string filename_8mA{bitstream_path + line + "_8mA.jic"};
    std::string filename_12mA{bitstream_path + line + "_12mA.jic"};

    int addr_4mA = get_first_pos(filename_4mA, filename_12mA);
    int addr_8mA = get_first_pos(filename_8mA, filename_12mA);

    std::cout << "  " << addr_4mA << ", " << addr_8mA << "\n";

    pt::ptree child;

    child.put("bit_4mA", addr_4mA);
    child.put("bit_8mA", addr_8mA);
    root.push_back(std::make_pair(line, child));
  }

  pt::write_json("pin_summary.json", root);
}
