## 2.0.7-rc.3
- Fix blue screen rendering issue in typeNode picture in picture scene

## 2.0.7-rc.2
- Fix abnormal issues with RTMP video recording

## 2.0.7-rc.1
- Add support for stopAsynchronous and releaseAsynchronous interfaces

## 2.0.7-rc.0
- Fix hardware decoder render bug

## 2.0.6
- HLS start broadcasting optimization
- Fix playback jitter issue

## 2.0.6-rc.6
- Fix the black screen issue caused by the use of hard decoding buffer

## 2.0.6-rc.5
- Provides interfaces for plugging and disconnecting audio devices for listening

## 2.0.6-rc.4
- Fix video recording crash issue
- Fix the problem of unsynchronized recording of video audio and image

## 2.0.6-rc.3
- fix:clear invaild audio data

## 2.0.6-rc.2
- Fixed the issue of callback not triggering after hard decoding playback completion
- Switch openssl version 3.4.0

## 2.0.6-rc.1
- Add support for video recording and screenshot functionality

## 2.0.6-rc.0
- Fix release crash issue

## 2.0.5
- 在DevEco Studio: NEXT Beta1-5.0.3.806, SDK: API12 Release (5.0.0.66)上验证通过

## 2.0.5-rc.4
- 修复蓝牙播放时音画不同步问题
- 修复线程未销毁问题
- 切换LogUtils类记录日志方式

## 2.0.5-rc.3
- assert异常崩溃改为异常return返回

## 2.0.5-rc.2
- 修复bug,无法旋转带有rotation信息的视频

## 2.0.5-rc.1
- 实现多实例播放

## 2.0.5-rc.0
- 修复音量设置不生效问题

## 2.0.4

- 修复因音频采样率设置错误导致的播放速度异常
- 添加对id为空字符串的处理
- 修改mediacodec_all_videos默认值为0

## 2.0.3

- 音频框架由OpenSLES切换OHAudio
- 新增音频焦点监听接口与取消监听接口
  - on(type: AudioInterrupt,  callback: Callback<InterruptEvent>)
  - off(type: AudioInterrupt)
- 修复2.0.3-rc.2、2.0.3-rc.3版本漏问题：切换依赖版本openssl1.0.2u -> openssl1.1.1w

## 2.0.3-rc.3

- 适配H265硬解码

## 2.0.3-rc.2

- 适配x86架构

## 2.0.3-rc.1

- 音频与XComponent解耦

## 2.0.3-rc.0
- 修复ArkTs语法问题--添加函数返回值类型

## 2.0.2
- 修复eglCreateWindowSurface接口兼容性问题：将window的format设置为与参数config的format一致

## 2.0.2-rc.0
- 修复不兼容API9问题

## 2.0.1
- 添加demo视频列表
- ArkTs语法整改
- 修复偶现因变量值被系统回收引起的播放异常问题
- 更换视频链接
- 修复demo问题：第二条视频播放异常与第三第四条视频无法加载
- demo添加循环播放、倍数播放功能
- 修复demo播放视频的进度条显示问题
- 修复ijkplayer可能崩溃的情况，播放添加http-header参数
- 适配SDK: API10

## 2.0.0
- 包管理工具由npm切换为ohpm
- 适配DevEco Studio: 3.1Beta2(3.1.0.400)
- 适配SDK: API9 Release(3.2.11.9)

## 1.0.5
- 适配DevEco Studio 3.1 Beta1版本
- 调整XComponent用法

## 1.0.2
- 添加支持直播rtsp协议

## 1.0.1
- 修复getMediaInfo()接口crash问题

## 1.0.0
- 发布ijkplayer项目
- 支持直播、点播 (直播支持hls、rtmp协议) 
- 支持播放、暂停、停止、重置、释放
- 支持快进、后退
- 支持倍数播放
- 支持循环播放
- 支持设置屏幕常亮
- 支持设置音量
- 支持FFmpeg软解码  
- 不支持硬解码

