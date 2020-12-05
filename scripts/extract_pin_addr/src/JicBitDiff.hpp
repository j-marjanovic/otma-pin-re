
// Copyright (c) 2020 Jan Marjanovic

#pragma once

#include <cstdint>

struct JicBitDiff {
  int addr;
  bool a, b;
};

std::ostream &operator<<(std::ostream &os, const JicBitDiff &bd) {
  os << "JicBitDiff{addr = " << bd.addr << ", a = " << std::hex << bd.a
     << ", b = " << bd.b << std::dec << "}";
  return os;
}