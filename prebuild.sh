#!/bin/bash

# Copyright (c) 2024 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# 执行该脚本时需进入到脚本所在目录
ROOT_DIR=$(pwd)
API_VERSION=12                                                              # 三方库对应API版本，用于记录SDK路径,必须和"compileSdkVersion"字段表示的API版本保持一致
SDK_DIR=$ROOT_DIR/../ohos-sdk-$API_VERSION/linux/$API_VERSION               # SDK路径（流水线环境中SDK路径）
LYCIUM_TOOLS_URL=https://gitee.com/openharmony-sig/tpc_c_cplusplus.git
LYCIUM_ROOT_DIR=$ROOT_DIR/tpc_c_cplusplus
LYCIUM_TOOLS_DIR=$LYCIUM_ROOT_DIR/lycium
LYCIUM_THIRDPARTY_DIR=$LYCIUM_ROOT_DIR/thirdparty
DEPENDS_DIR=$ROOT_DIR/doc                                                   # 依赖库编译脚本在仓库中的位置
FFMPEG_NAME=FFmpeg-ff4.0                                                    # 依赖库名
LIBYUV_NAME=libyuv-ijk                                                      # 依赖库名
SOUNDTOUCH_NAME=soundtouch-ijk                                              # 依赖库名
OPESSL_NAME=openssl_1_1_1w                                                  # FFmpeg的依赖库名，需和依赖库一起安装
OPENH264_NAME=openh264                                                      # FFmpeg的依赖库名，需和依赖库一起安装

CI_OUTPUT_DIR=$ROOT_DIR/../out/tpc/                                         # hap/har安装目录

LIBS_NAME=("FFmpeg-ff4.0" "libyuv-ijk" "soundtouch-ijk" "openssl_1_1_1w" "openh264")
PACKAGE_NAME=("FFmpeg-ff4.0-ijk0.8.8-20210426-001.tar.gz" "yuv-ijk-r0.2.1-dev.zip" "soundtouch-ijk-r0.1.2-dev.zip" "openssl-OpenSSL_1_1_1w.zip" "openh264-2.4.1.tar.gz")

function prepare_lycium_tools()
{
    local commands=("gcc" "make" "cmake" "pkg-config" "autoconf" "autoreconf" "automake" "patch" "libtool" "autopoint" "gperf" \
    "tcl8.6-dev" "wget" "unzip" "gccgo-go" "flex " "bison" "premake4" "python3" "python3-pip" \
    "ninja-build" "meson" "sox" "gfortran" "subversion" "build-essential" "module-assistant" " gcc-multilib" \
    "g++-multilib" "libltdl7-dev" "cabextract" "libboost-all-dev" "libxml2-utils" "gettext" "libxml-libxml-perl" \
    "libxml2" "libxml2-dev" "libxml-parser-perl" "texinfo" "libtool-bin" "xmlto" "po4a" "yasm" "nasm" "xutils-dev" \
    "libx11-dev" "xtrans-dev" "gfortran-arm-linux-gnueabi" "gfortran-aarch64-linux-gnu")

    apt update >> /dev/null

    for cmd in ${commands[@]}
    do
        which $cmd >> /dev/null
        if [ $? -ne 0 ]
        then
            echo "install $cmd"
            apt install $cmd -y >> /dev/null
        fi
    done
}

function prepare_lycium()
{
    if [ -d $LYCIUM_ROOT_DIR ]
    then
        rm -rf $LYCIUM_ROOT_DIR
    fi

    git clone $LYCIUM_TOOLS_URL -b support_x86 --depth=1
    if [ $? -ne 0 ]
    then
        return 1
    fi

    cd $LYCIUM_TOOLS_DIR/Buildtools
    tar -zxvf toolchain.tar.gz
    if [ $? -ne 0 ]
    then
        echo "unpack sdk toolchain failed!!"
        cd $OLDPWD
        return 1
    fi

    cp toolchain/* $SDK_DIR/native/llvm/bin/

    prepare_lycium_tools
    ret=$?
    cd $OLDPWD

    return $ret
}

function copy_depends()
{
    local dir=$1
    local name=$2

    if [ -d $LYCIUM_THIRDPARTY_DIR/$name ]
    then
        rm -rf $LYCIUM_THIRDPARTY_DIR/$name
    fi
    cp -arf $dir/$name $LYCIUM_THIRDPARTY_DIR/
}

function prepare_depends()
{
    copy_depends $DEPENDS_DIR $LIBYUV_NAME
    copy_depends $DEPENDS_DIR $SOUNDTOUCH_NAME
}

function check_sdk()
{
    if [ ! -d $SDK_DIR ]
    then
        return 1
    fi

    export OHOS_SDK=$SDK_DIR
    return 0
}

function check_copy_shasum()
{
    local libpath=$1
    local pack_name=$2
    local libname=$3

    cd $LYCIUM_THIRDPARTY_DIR/$libpath
    if [ ! -f ./SHA512SUM ]
    then
        sha512sum $pack_name > ./SHA512SUM
    fi
    cp ./SHA512SUM $LYCIUM_TOOLS_DIR/usr/$libname/

    cd $OLDPWD
}

function install_shasum()
{
    check_copy_shasum $FFMPEG_NAME ${PACKAGE_NAME[0]} $FFMPEG_NAME
    check_copy_shasum $LIBYUV_NAME ${PACKAGE_NAME[1]} yuv
    check_copy_shasum $SOUNDTOUCH_NAME ${PACKAGE_NAME[2]} soundtouch
    check_copy_shasum $OPESSL_NAME ${PACKAGE_NAME[3]} $OPESSL_NAME
    check_copy_shasum $OPENH264_NAME ${PACKAGE_NAME[4]} $OPENH264_NAME
}
function start_build()
{
    local result=0
    cd $LYCIUM_TOOLS_DIR
    if [ $? -ne 0 ]
    then
        return 1
    fi

    bash build.sh $FFMPEG_NAME $LIBYUV_NAME $SOUNDTOUCH_NAME
    result=$?
    cd $OLDPWD
    return $result
}

function install_depends()
{
    local install_dir=$ROOT_DIR/ijkplayer/src/main/cpp/third_party/
    cp -arf $LYCIUM_TOOLS_DIR/usr/$FFMPEG_NAME $install_dir/ffmpeg/ffmpeg
    if [ $? -ne 0 ]
    then
        echo "FFmpeg build failed!"
        return 1
    fi
    cp -arf $LYCIUM_TOOLS_DIR/usr/yuv $install_dir/yuv
    if [ $? -ne 0 ]
    then
        echo "yuv build failed!"
        return 1
    fi
    cp -arf $LYCIUM_TOOLS_DIR/usr/$OPESSL_NAME $install_dir/openssl
    if [ $? -ne 0 ]
    then
        echo "FFmpeg depends openssl build failed!"
        return 1
    fi
    cp -arf $LYCIUM_TOOLS_DIR/usr/soundtouch $install_dir/soundtouch
    if [ $? -ne 0 ]
    then
        echo "soundtouch build failed!"
        return 1
    fi
    cp -arf $LYCIUM_TOOLS_DIR/usr/openh264 $install_dir/openh264
    if [ $? -ne 0 ]
    then
        echo "FFmpeg depends openh264 build failed!"
        return 1
    fi

    if [ -d $CI_OUTPUT_DIR ]
    then
        cp -arf $LYCIUM_TOOLS_DIR/usr/$FFMPEG_NAME $CI_OUTPUT_DIR
        cp -arf $LYCIUM_TOOLS_DIR/usr/yuv $CI_OUTPUT_DIR
        cp -arf $LYCIUM_TOOLS_DIR/usr/$OPESSL_NAME $CI_OUTPUT_DIR
        cp -arf $LYCIUM_TOOLS_DIR/usr/soundtouch $CI_OUTPUT_DIR
        cp -arf $LYCIUM_TOOLS_DIR/usr/openh264 $CI_OUTPUT_DIR
    fi

    return 0
}

function prebuild()
{
    check_sdk
    if [ $? -ne 0 ]
    then
        echo "ERROR: check_sdk failed!!!"
        return 1
    fi
    prepare_lycium
    if [ $? -ne 0 ]
    then
        echo "ERROR: prepare_lycium failed!!!"
        return 1
    fi
    prepare_depends
    start_build
    if [ $? -ne 0 ]
    then
        echo "ERROR: start_build failed!!!"
        return 1
    fi
    install_shasum
    install_depends
    if [ $? -ne 0 ]
    then
        echo "ERROR: install depends failed!!!"
        return 1
    fi
    echo "prebuild success!!"

    return 0
}

prebuild $*
ret=$?
echo "ret = $ret"
exit $ret

#EOF
