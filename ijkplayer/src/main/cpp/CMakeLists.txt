# the minimum version of CMake.
cmake_minimum_required(VERSION 3.4.1)
project(ijkplayer)

add_subdirectory(ijksdl)
add_subdirectory(ijkplayer)

add_definitions(-DOHOS_PLATFORM)

add_library(ijkplayer_napi SHARED
            napi/ijkplayer_napi.cpp
           proxy/ijkplayer_napi_proxy.c
           utils/hashmap/data_struct.c
           utils/ffmpeg/custom_ffmpeg_log.c
           utils/napi/napi_utils.cpp
            )

include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/ijkplayer)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/ijksdl)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/proxy)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/napi)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/utils/napi)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/third_party/ffmpeg/include)


add_library(ijkffmpeg SHARED IMPORTED )

set_target_properties(ijkffmpeg
        PROPERTIES IMPORTED_LOCATION
        ${CMAKE_SOURCE_DIR}/../../../libs/${OHOS_ARCH}/libijkffmpeg.z.so)

target_link_libraries(ijkplayer_napi PUBLIC ijkplayer)
target_link_libraries(ijkplayer_napi PUBLIC ijksdl)
target_link_libraries(ijkplayer_napi PUBLIC ijkffmpeg)
target_link_libraries(ijkplayer_napi PUBLIC EGL)
target_link_libraries(ijkplayer_napi PUBLIC GLESv3)
target_link_libraries(ijkplayer_napi PUBLIC hilog_ndk.z)
target_link_libraries(ijkplayer_napi PUBLIC ace_ndk.z)
target_link_libraries(ijkplayer_napi PUBLIC ace_napi.z)
target_link_libraries(ijkplayer_napi PUBLIC libc++.a)
target_link_libraries(ijkplayer_napi PUBLIC uv)
