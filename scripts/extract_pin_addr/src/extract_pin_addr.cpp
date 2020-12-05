
// Copyright (c) 2020 Jan Marjanovic

#include <cstddef>
#include <iostream>
#include <iterator>
#include <vector>

#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include <boost/log/core.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/trivial.hpp>

#include "JicBitDiff.hpp"
#include "JicBitstream.hpp"

namespace logging = boost::log;

int main() {

  logging::core::get()->set_filter(logging::trivial::severity >=
                                   logging::trivial::debug);

  std::ifstream infile{"../../../resources/first_16.txt"};
  std::string line;

  namespace pt = boost::property_tree;
  pt::ptree root;

  std::string bitstream_path = "../../../bitstreams/2p5V/pin_ident_PIN_";

  while (infile >> line) {
    std::cout << "line = " << line << "\n";
    JicBitstream jic_4mA{bitstream_path + line + "_4mA.jic"};
    JicBitstream jic_8mA{bitstream_path + line + "_8mA.jic"};
    JicBitstream jic_12mA{bitstream_path + line + "_12mA.jic"};

    std::vector<JicBitDiff> diff_4mA = jic_4mA ^ jic_12mA;
    std::vector<JicBitDiff> diff_8mA = jic_8mA ^ jic_12mA;

    std::cout << "  " << diff_4mA[0] << ", " << diff_8mA[1] << "\n";

    pt::ptree child;

    child.put("bit_4mA", diff_4mA[0].addr);
    child.put("bit_8mA", diff_8mA[0].addr);
    root.push_back(std::make_pair(line, child));
  }

  pt::write_json("pin_summary.json", root);
}
