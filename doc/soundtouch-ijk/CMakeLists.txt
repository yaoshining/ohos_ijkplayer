cmake_minimum_required(VERSION 3.4.1)
project(soundtouch)

include_directories(${CMAKE_CURRENT_LIST_DIR})
include_directories(${CMAKE_CURRENT_LIST_DIR}/include)

add_library(soundtouch  STATIC source/SoundTouch/AAFilter.cpp
                      source/SoundTouch/FIFOSampleBuffer.cpp
                      source/SoundTouch/FIRFilter.cpp
                      source/SoundTouch/cpu_detect_x86.cpp
                      source/SoundTouch/sse_optimized.cpp
                      source/SoundTouch/RateTransposer.cpp
                      source/SoundTouch/InterpolateCubic.cpp
                      source/SoundTouch/InterpolateLinear.cpp
                      source/SoundTouch/InterpolateShannon.cpp
                      source/SoundTouch/TDStretch.cpp
                      source/SoundTouch/BPMDetect.cpp
                      source/SoundTouch/PeakFinder.cpp
                      source/SoundTouch/SoundTouch.cpp
                      source/SoundTouch/mmx_optimized.cpp
                      ijksoundtouch_wrap.cpp)




