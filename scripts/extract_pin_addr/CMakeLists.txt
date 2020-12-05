cmake_minimum_required(VERSION 3.5)
project(OtmaPinReTools VERSION 0.1.0)

find_package(Boost 1.71 COMPONENTS log REQUIRED)

add_executable(extract_pin_addr)
target_sources(extract_pin_addr PRIVATE src/extract_pin_addr.cpp)
target_compile_options(extract_pin_addr PRIVATE "-O2")
target_compile_features(extract_pin_addr PUBLIC cxx_std_17)
target_link_libraries(extract_pin_addr Boost::log)
