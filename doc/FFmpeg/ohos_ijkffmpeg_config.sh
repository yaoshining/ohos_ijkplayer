# FFmpeg build configure

#!/bin/bash

FFMPEG_PATH=$1
FFMPEG_OUT_PATH=$2
echo "***开始准备编译ffmpeg***"
echo $FFMPEG_OUT_PATH
echo $FFMPEG_PATH

FF_CONFIG_OPTIONS="
    --disable-gpl
    --disable-nonfree
    --disable-runtime-cpudetect
    --disable-gray
    --disable-swscale-alpha
    --disable-ffmpeg
    --disable-ffplay
    --disable-ffprobe
    --disable-doc
    --disable-htmlpages
    --disable-manpages
    --disable-podpages
    --disable-lzma
    --disable-asm
    --disable-programs
    --disable-doc
    --disable-debug
    --disable-pixelutils
    --disable-avdevice
    --disable-avfilter
    --disable-avresample
    --disable-postproc
    --disable-devices
    --disable-bsfs
    --disable-iconv
    --disable-xlib
    --disable-zlib
    --disable-cuvid
    --disable-cuda
    --disable-libxcb
    --disable-libxcb_shape
    --disable-libxcb_shm
    --disable-libxcb_xfixes
    --disable-sdl2
    --disable-hwaccels
    --disable-muxers
    --disable-demuxers
    --disable-parsers
    --disable-protocols
    --disable-bzlib
    --disable-vaapi
    --disable-vdpau
    --disable-dwt
    --disable-lsp
    --disable-lzo
    --disable-faan
    --disable-encoders
    --disable-decoders
    --enable-network
    --enable-protocol=file,http,https,tcp,httpproxy,rtmp,rtp
    --enable-demuxer=hls,flv,live_flv,mp3,aac,ape,flac,ogg,wav,mov,mpegts,rtmp,rtsp,sdp,rtp
    --enable-muxer=mp4,h264,mp3
    --enable-parser=h263,mpeg4video,vp8,vp9,mp3,h264
    --enable-parser=mpegaudio,aac,aac_latm
    --enable-decoder=h263,h264,mpeg2video,mpeg4,vp8,vp9
    --enable-decoder=mp3,mp3float,aac,aac_latm,ape,flac,vorbis,opus
    --enable-encoder=aac,aac_latm,opus
    --enable-encoder=mpeg4,h263,mp3
    --enable-openssl
"

FF_CONFIG_OPTIONS=`echo $FF_CONFIG_OPTIONS`

${FFMPEG_PATH}/configure ${FF_CONFIG_OPTIONS}
sed -i 's/HAVE_SYSCTL 1/HAVE_SYSCTL 0/g' ijkffmpeg_config.h
sed -i 's/HAVE_SYSCTL=yes/!HAVE_SYSCTL=yes/g' ./ijkffmpeg_ffbuild/config.mak
sed -i 's/HAVE_GLOB 1/HAVE_GLOB 0/g' ijkffmpeg_config.h
sed -i 's/HAVE_GLOB=yes/!HAVE_GLOB=yes/g' ijkffmpeg_config.h
sed -i 's/HAVE_GMTIME_R 1/HAVE_GMTIME_R 0/g' ijkffmpeg_config.h
sed -i 's/HAVE_LOCALTIME_R 1/HAVE_LOCALTIME_R 0/g' ijkffmpeg_config.h
sed -i 's/HAVE_PTHREAD_CANCEL 1/HAVE_PTHREAD_CANCEL 0/g' ijkffmpeg_config.h
sed -i 's/HAVE_VALGRIND_VALGRIND_H 1/HAVE_VALGRIND_VALGRIND_H 0/g' ijkffmpeg_config.h

tmp_file=".ijkffmpeg_tmpfile"
## remove invalid restrict define
sed 's/#define av_restrict restrict/#define av_restrict/' ./ijkffmpeg_config.h >$tmp_file
mv $tmp_file ./ijkffmpeg_config.h

## replace original FFMPEG_CONFIGURATION define with $FF_CONFIG_OPTIONS
sed '/^#define FFMPEG_CONFIGURATION/d' ./ijkffmpeg_config.h >$tmp_file
mv $tmp_file ./ijkffmpeg_config.h
total_line=`wc -l ./ijkffmpeg_config.h | cut -d' ' -f 1`
tail_line=`expr $total_line - 3`
head -3 ijkffmpeg_config.h > $tmp_file
echo "#define FFMPEG_CONFIGURATION \"${FF_CONFIG_OPTIONS}\"" >> $tmp_file
tail -$tail_line ijkffmpeg_config.h >> $tmp_file
mv $tmp_file ./ijkffmpeg_config.h

rm -f config.err

## rm BUILD_ROOT information
sed '/^BUILD_ROOT=/d' ./ijkffmpeg_ffbuild/config.mak > $tmp_file
rm -f ./ijkffmpeg_ffbuild/config.mak
mv $tmp_file ./ijkffmpeg_ffbuild/config.mak

## rm amr-eabi-gcc
sed '/^CC=arm-eabi-gcc/d' ./ijkffmpeg_ffbuild/config.mak > $tmp_file
rm -f ./ijkffmpeg_ffbuild/config.mak
mv $tmp_file ./ijkffmpeg_ffbuild/config.mak

## rm amr-eabi-gcc
sed '/^AS=arm-eabi-gcc/d' ./ijkffmpeg_ffbuild/config.mak > $tmp_file
rm -f ./ijkffmpeg_ffbuild/config.mak
mv $tmp_file ./ijkffmpeg_ffbuild/config.mak


## rm amr-eabi-gcc
sed '/^LD=arm-eabi-gcc/d' ./ijkffmpeg_ffbuild/config.mak > $tmp_file
rm -f ./ijkffmpeg_ffbuild/config.mak
mv $tmp_file ./ijkffmpeg_ffbuild/config.mak

## rm amr-eabi-gcc
sed '/^DEPCC=arm-eabi-gcc/d' ./ijkffmpeg_ffbuild/config.mak > $tmp_file
rm -f ./ijkffmpeg_ffbuild/config.mak
mv $tmp_file ./ijkffmpeg_ffbuild/config.mak

sed -i 's/restrict restrict/restrict /g' ijkffmpeg_config.h

sed -i '/getenv(x)/d' ijkffmpeg_config.h
sed -i 's/HAVE_DOS_PATHS 0/HAVE_DOS_PATHS 1/g' ijkffmpeg_config.h

mv ijkffmpeg_config.h ${FFMPEG_OUT_PATH}/config.h
mv ./ijkffmpeg_ffbuild/config.mak ${FFMPEG_OUT_PATH}/config.mak
mv -f libavcodec_ijk ${FFMPEG_OUT_PATH}
mv -f libavformat_ijk ${FFMPEG_OUT_PATH}
mv -f libavutil_ijk ${FFMPEG_OUT_PATH}
mv -f libavdevice_ijk ${FFMPEG_OUT_PATH}
mv -f libavfilter_ijk ${FFMPEG_OUT_PATH}
cd ${FFMPEG_OUT_PATH}
mv libavcodec_ijk libavcodec
mv libavformat_ijk libavformat
mv libavutil_ijk libavutil
mv libavdevice_ijk libavdevice
mv libavfilter_ijk libavfilter
#rm -rf ./ffbuild
echo "***编译FFmpeg准备结束***"

# other work need to be done manually
cat <<!EOF
#####################################################
                    ****NOTICE****
You need to modify the file config.mak and delete
all full path string in macro:
SRC_PATH, SRC_PATH_BARE, BUILD_ROOT, LDFLAGS.
Please refer to the old version of config.mak to
check how to modify it.
#####################################################
!EOF
