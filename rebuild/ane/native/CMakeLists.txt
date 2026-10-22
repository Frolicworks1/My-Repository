cmake_minimum_required(VERSION 3.22)
project(ttpixel_core LANGUAGES C CXX)

add_library(ttpixel_core SHARED ttpixel_core.cpp)
target_include_directories(ttpixel_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(ttpixel_core PRIVATE cxx_std_17)
target_compile_options(ttpixel_core PRIVATE -Wall -Wextra -Werror)
set_target_properties(ttpixel_core PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
)
