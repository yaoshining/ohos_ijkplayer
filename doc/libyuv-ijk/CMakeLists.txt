cmake_minimum_required(VERSION 3.4.1)
project(yuv)

include_directories(${CMAKE_CURRENT_LIST_DIR})
include_directories(${CMAKE_CURRENT_LIST_DIR}/include)

if(${OHOS_ARCH} STREQUAL "armeabi-v7a")

add_library(yuv  STATIC source/compare.cc
                      source/compare_common.cc
                      source/compare_posix.cc
                      source/convert.cc
                      source/convert_argb.cc
                      source/convert_from.cc
                      source/convert_from_argb.cc
                      source/convert_to_argb.cc
                      source/convert_to_i420.cc
                      source/cpu_id.cc
                      source/format_conversion.cc
                      source/planar_functions.cc
                      source/rotate.cc
                      source/rotate_argb.cc
                      source/rotate_mips.cc
                      source/row_any.cc
                      source/row_common.cc
                      source/row_mips.cc
                      source/row_posix.cc
                      source/scale.cc
                      source/scale_argb.cc
                      source/scale_common.cc
                      source/scale_mips.cc
                      source/scale_posix.cc
                      source/video_common.cc)

else()
add_library(yuv  STATIC source/compare.cc
                      source/compare_common.cc
                      source/compare_posix.cc
                      source/convert.cc
                      source/convert_argb.cc
                      source/convert_from.cc
                      source/convert_from_argb.cc
                      source/convert_to_argb.cc
                      source/convert_to_i420.cc
                      source/cpu_id.cc
                      source/format_conversion.cc
                      source/planar_functions.cc
                      source/rotate.cc
                      source/rotate_argb.cc
                      source/rotate_mips.cc
                      source/row_any.cc
                      source/row_common.cc
                      source/row_mips.cc
                      source/row_posix.cc
                      source/scale.cc
                      source/scale_argb.cc
                      source/scale_common.cc
                      source/scale_mips.cc
                      source/scale_posix.cc
                      source/video_common.cc
                      source/compare_neon64.cc
                      source/rotate_neon64.cc
                      source/row_neon64.cc
                      source/scale_neon64.cc)
endif()





