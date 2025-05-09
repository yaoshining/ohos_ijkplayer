# ijkplayer

## Introduction
>  ijkplayer is an FFmpeg-based video player that can be used in the OpenHarmony system.

## Demo
<img src="preview.gif" width="100%"/>

## How to Build

### FFmpeg soundtouch YUV openh264 dependency

1. FFmpeg: FFmpeg version (ff4.0--ijk0.8.8--20210426--001)[FFmpeg source code link](https://github.com/bilibili/FFmpeg/tags) based on BiliBili supports the cross-compilation of library and header files. For details about the compilation, see [FFmpeg-ff4.0 Compilation Guide](https://gitcode.com/openharmony-sig/tpc_c_cplusplus/blob/support_x86/thirdparty/FFmpeg-ff4.0/README_zh.md).

   1. After the compilation is successful, the **FFmpeg-ff4.0 folder** is generated in **lycium\usr** and renamed **ffmpeg**.

2. soudtouch: soudtouch version (ijk-r0.1.2-dev):[soundtouch source code link] (https://github.com/bilibili/soundtouch/branches) based on BiliBili supports the cross-compilation of library and header files.

   1. Copy the **soundtouch-ijk** folder in the **doc** directory to the **thirdparty** directory. Run the **./build.sh soundtouch-ijk** command in the **lycium** folder to compile the static library and header file of the soundtouch in the **lycium\usr** directory.

3. YUV: YUV version (ijk-r0.2.1-dev):[YUV source code link](https://github.com/bilibili/libyuv/branches) based on BiliBili supports the cross-compilation of library and header files.
   1. Copy the **libyuv-ijk** folder in the **doc** directory to the **thirdparty** directory. In the **lycium** folder, run the **./build.sh libyuv-ijk** command to compile the YUV static library and header file in the **lycium\usr** directory.

4. openh264: Based on version (openh264-2.4.1): [openh264 source code link](https://github.com/cisco/openh264/releases) OpenH264 requires cross compilation of the outbound and header files. Compile script can refer to [openh264](https://gitcode.com/openharmony-sig/tpc_c_cplusplus/blob/support_x86/thirdparty/openh264) After compilation, the output file is located in the openh264 folder in the **lycium\usr** directory.

5. Copy the **ffmpeg** folder generated after compilation to **ijkplayer/src/main/cpp/third_party/ffmpeg**.

6. Copy the **openssl**, **soundtouch**, **yuv**, and **openh264** folders generated after compilation to the **ijkplayer/src/main/cpp/third_party** directory of the project, as shown in the following figure.

![img.png](image/img.png)

### How to Build

1. Download the dependency SDK through DevEco Studio. Specifically, on DevEco Studio, choose **Tools > SDK Manager > OpenHarmony SDK**, select **native**, and set the API version to 9 or later to download the SDK.

2. Select the RK3568 development board. The ROM download address of the development board is **https://ci.openharmony.cn/workbench/cicd/dailybuild/dailylist**. Choose the latest ROM version.

3. Use **git clone** to download the source code. Do not download the source code directly from the Gitee web page.

## How to Install
```shell
ohpm install @ohos/ijkplayer
```
## How to Use
```
   import { IjkMediaPlayer } from "@ohos/ijkplayer";
   import type { OnPreparedListener } from "@ohos/ijkplayer";
   import type { OnVideoSizeChangedListener } from "@ohos/ijkplayer";
   import type { OnCompletionListener } from "@ohos/ijkplayer";
   import type { OnBufferingUpdateListener } from "@ohos/ijkplayer";
   import type { OnErrorListener } from "@ohos/ijkplayer";
   import type { OnInfoListener } from "@ohos/ijkplayer";
   import type { OnSeekCompleteListener } from "@ohos/ijkplayer";
   import { LogUtils } from "@ohos/ijkplayer";
```
### Configuring the XComponent control on the UI
```
    XComponent({
      id: 'xcomponentId',
      type: 'surface',
      libraryname: 'ijkplayer_napi'
    })
    .onLoad((context) => {
      this.initDelayPlay(context);
     })
     .onDestroy(() => {
     })
     .width('100%')
     .aspectRatio(this.aspRatio)
```

### Playback setting
```
    //Singleton mode
    let mIjkMediaPlayer = IjkMediaPlayer.getInstance();
    //Multiton mode
    let mIjkMediaPlayer = new IjkMediaPlayer();
    // If a video is played, call the **setContext** interface. Parameter 1 is the context called back by the XComponent, and optional parameter 2 is the ID of the XComponent.
    mIjkMediaPlayer.setContext(this.mContext, "xcomponentId");
    // If only audio is played, call the **setAudioId** interface. The parameter is the ID of the audio object.
    // mIjkMediaPlayer.setAudioId('audioIjkId');
    // Set the debug mode.
    mIjkMediaPlayer.setDebug(true);
    // Initialize configuration.
    mIjkMediaPlayer.native_setup();
    // Set the video source.
    mIjkMediaPlayer.setDataSource(url); 
    // Set the HTTP request header of the video source.
    let headers =  new Map([
      ["user_agent", "Mozilla/5.0 BiliDroid/7.30.0 (bbcallen@gmail.com)"],
      ["referer", "https://www.bilibili.com"]
    ]);
    mIjkMediaPlayer.setDataSourceHeader(headers);
    // Use precise frame searching. For example, after the playback is dragged, the system searches for the nearest key frame for playback. It is very likely that the position of the key frame is not the position after the dragging but the position before the dragging, which can be solved by setting this parameter.
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "enable-accurate-seek", "1");
    // Size of the buffer for pre-reading data
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max-buffer-size", "102400");
    // Minimum number of frames to stop pre-reading
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "min-frames", "100");
    // Start preloading.
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "start-on-prepared", "1");
    // Set the playback of data without any cache.
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "packet-buffering", "0");
    // Frame skipping. When the CPU processing is slow, frame skipping is performed to ensure that the image and audio are synchronized during the playback.
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "framedrop", "5");
    // The maximum cache duration is 3s. Sometimes, data of several seconds is received in a short period of time due to network fluctuation.
    // Therefore, some packets will be lost to ensure that the delay is not accumulated.
    // This is irrelevant to the third parameter **packet-buffering**.
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max_cached_duration", "3000");
    // Unlimited stream receiving
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "infbuf", "1");
    // Screen on
    mIjkMediaPlayer.setScreenOnWhilePlaying(true);
    // Set the timeout.
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "timeout", "10000000");
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "connect_timeout", "10000000");
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "listen_timeout", "10000000");
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "addrinfo_timeout", "10000000");
    mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "dns_cache_timeout", "10000000");
    
    let mOnVideoSizeChangedListener: OnVideoSizeChangedListener = {
      onVideoSizeChanged(width: number, height: number, sar_num: number, sar_den: number) {
        that.aspRatio = width / height;
        LogUtils.getInstance()
          .LOGI("setOnVideoSizeChangedListener-->go:" + width + "," + height + "," + sar_num + "," + sar_den)
        that.hideLoadIng();
      }
    }
    mIjkMediaPlayer.setOnVideoSizeChangedListener(mOnVideoSizeChangedListener);
    let mOnPreparedListener: OnPreparedListener = {
      onPrepared() {
        LogUtils.getInstance().LOGI("setOnPreparedListener-->go");
      }
    }
    mIjkMediaPlayer.setOnPreparedListener(mOnPreparedListener);

    let mOnCompletionListener: OnCompletionListener = {
      onCompletion() {
        LogUtils.getInstance().LOGI("OnCompletionListener-->go")
        that.currentTime = that.stringForTime(mIjkMediaPlayer.getDuration());
        that.progressValue = PROGRESS_MAX_VALUE;
        that.stop();
      }
    }
    mIjkMediaPlayer.setOnCompletionListener(mOnCompletionListener);

    let mOnBufferingUpdateListener: OnBufferingUpdateListener = {
      onBufferingUpdate(percent: number) {
        LogUtils.getInstance().LOGI("OnBufferingUpdateListener-->go:" + percent)
      }
    }
    mIjkMediaPlayer.setOnBufferingUpdateListener(mOnBufferingUpdateListener);

    let mOnSeekCompleteListener: OnSeekCompleteListener = {
      onSeekComplete() {
        LogUtils.getInstance().LOGI("OnSeekCompleteListener-->go")
        that.startPlayOrResumePlay();
      }
    }
    mIjkMediaPlayer.setOnSeekCompleteListener(mOnSeekCompleteListener);

    let mOnInfoListener: OnInfoListener = {
      onInfo(what: number, extra: number) {
        LogUtils.getInstance().LOGI("OnInfoListener-->go:" + what + "===" + extra)
      }
    }
    mIjkMediaPlayer.setOnInfoListener(mOnInfoListener);

    let mOnErrorListener: OnErrorListener = {
      onError(what: number, extra: number) {
        LogUtils.getInstance().LOGI("OnErrorListener-->go:" + what + "===" + extra)
        that.hideLoadIng();
        prompt.showToast({
          message: "Sorry for the playback error. The system is not running properly."
        });
      }
    }
    mIjkMediaPlayer.setOnErrorListener(mOnErrorListener);

    mIjkMediaPlayer.setMessageListener();

    mIjkMediaPlayer.prepareAsync();

    mIjkMediaPlayer.start();
```
### Pause
```
   mIjkMediaPlayer.pause();
```
### Stop
```
   mIjkMediaPlayer.stop();
```
### Reset
```
   mIjkMediaPlayer.reset();
```
### Release
```
   mIjkMediaPlayer.release();
```
### Fast-forward and Rewind
```
   mIjkMediaPlayer.seekTo(msec);
```
### Playback Speed
```
   mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "soundtouch", "1");
   mIjkMediaPlayer.setSpeed("2f");
```
### Screen on
```
   mIjkMediaPlayer.setScreenOnWhilePlaying(true);
```
### Loop
```
   mIjkMediaPlayer.setLoopCount(true);
```
### Volume
```
   mIjkMediaPlayer.setVolume(leftVolume, rightVolume);
```
### Audio Focus Monitoring
```
   import { InterruptEvent, InterruptHintType } from '@ohos/ijkplayer/src/main/ets/ijkplayer/IjkMediaPlayer';
   import { Callback } from '@ohos.base';
   // Set callback processing when the audio focus changes.
   let event:  Callback<InterruptEvent> = (event) => {
     console.info(`event: ${JSON.stringify(event)}`);
     if (event.hintType === InterruptHintType.INTERRUPT_HINT_PAUSE) {
       this.pause();
     } else if (event.hintType === InterruptHintType.INTERRUPT_HINT_RESUME) {
       this.startPlayOrResumePlay();
     } else if (event.hintType === InterruptHintType.INTERRUPT_HINT_STOP) {
       this.stop();
     }
   }
   // Set listening for audio interruption events.
   mIjkMediaPlayer.on('audioInterrupt', event);

   // Unsubscribes from audio interruption events.
   mIjkMediaPlayer.off('audioInterrupt');
```

### Enabling Hardware Decoding
```
   // Enable H.264 and H.265 hardware decoding.
   ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "mediacodec-all-videos", "1");
   // Enable H.265 hardware decoding.
   ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "mediacodec-hevc", "1");
```

### Enable video recording
```
    let recordSaveFilePath = getContext(this).cacheDir + "/record.mp4";
    let result = this.mIjkMediaPlayer.startRecord(recordSaveFilePath);
    prompt.showToast({
      message: result ? "start record success" : "start record failed"
    });
```

### Get recording status
```
    let isRecord = this.mIjkMediaPlayer.isRecord();
    prompt.showToast({
      message: isRecord ? "recordIng" : "record not enabled"
    });
```

### Stop video recording
```
    // Permission is required to save the album: ohos.permission.WRITE_IMAGEVIDEO
    this.mIjkMediaPlayer.stopRecord().then((result) => {
      if(!result){
        prompt.showToast({
          message: "stop record failed"
        });
        return;
      }
      let atManager = abilityAccessCtrl.createAtManager();
      atManager.requestPermissionsFromUser(getContext(that), ['ohos.permission.WRITE_IMAGEVIDEO']).then(async () => {
        let photoType: photoAccessHelper.PhotoType = photoAccessHelper.PhotoType.VIDEO;
        let extension:string = 'mp4';
        let options: photoAccessHelper.CreateOptions = {
          title: "record_"+new Date().getTime()+""
        }
        let phAccessHelper = photoAccessHelper.getPhotoAccessHelper(getContext(that));
        phAccessHelper.createAsset(photoType, extension, options, (err, uri) => {
          if (uri !== undefined) {
            let recordFile = fs.openSync(that.recordSaveFilePath);
            let albumFile = fs.openSync(uri,fs.OpenMode.READ_WRITE);
            fs.copyFileSync(recordFile.fd,albumFile.fd);
            fs.closeSync(recordFile);
            fs.closeSync(albumFile);
            prompt.showToast({
              message: "stop record success"
            });
          } else {
            prompt.showToast({
              message: "stop record failed"
            });
          }
        });
      })
    })
```

### screenshot
```
    // Permission is required to save the album: ohos.permission.WRITE_IMAGEVIDEO
    let saveFilePath = getContext(this).cacheDir + "/screen.jpg";
    this.mIjkMediaPlayer.screenshot(saveFilePath).then((result) => {
      if(!result) {
        prompt.showToast({
          message: "screenshot failed"
        });
        return;
      }
      let atManager = abilityAccessCtrl.createAtManager();
      atManager.requestPermissionsFromUser(getContext(that), ['ohos.permission.WRITE_IMAGEVIDEO']).then(async () => {
        let photoType: photoAccessHelper.PhotoType = photoAccessHelper.PhotoType.IMAGE;
        let extension:string = 'jpg';
        let options: photoAccessHelper.CreateOptions = {
          title: "screenshot_"+new Date().getTime()+""
        }
        let phAccessHelper = photoAccessHelper.getPhotoAccessHelper(getContext(that));
        phAccessHelper.createAsset(photoType, extension, options, (err, uri) => {
          if (uri !== undefined) {
            let screenshotFile = fs.openSync(saveFilePath);
            let albumFile = fs.openSync(uri,fs.OpenMode.READ_WRITE);
            fs.copyFileSync(screenshotFile.fd,albumFile.fd);
            fs.closeSync(screenshotFile);
            fs.closeSync(albumFile);
            prompt.showToast({
              message: "screenshot success"
            });
          } else {
            prompt.showToast({
              message: "screenshot failed"
            });
          }
        });
      })
    });
```

### Audio device disconnection and connection monitoring
```
   import { InterruptEvent, InterruptHintType } from '@ohos/ijkplayer/src/main/ets/ijkplayer/IjkMediaPlayer';
   import { Callback } from '@ohos.base';
   // Handling callbacks for audio device disconnection
   let deviceChangeEvent: Callback<InterruptEvent> = (event) => {
      LogUtils.getInstance().LOGI(`deviceChange event: ${JSON.stringify(event)}`);
      if (event.reason === DeviceChangeReason.REASON_NEW_DEVICE_AVAILABLE) { // Audio device connection
        this.pause();
      } else if (event.reason === DeviceChangeReason.REASON_OLD_DEVICE_UNAVAILABLE) { // Audio device is disconnected
        this.pause();
      } 
    }
    // Subscribe to audio device disconnect and connection events
    this.mIjkMediaPlayer.on('deviceChange', deviceChangeEvent);

   // Unsubscribe from audio device disconnect and connection events
   mIjkMediaPlayer.off('audioInterrupt');
```

### HLS start broadcasting optimization
```
// Enabling hls start optimization is turned off by default
this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "fetch_first", "on");
```

## Available APIs

### IjkMediaPlayer.getInstance()
| API                          | Parameter                                                          | Return Value              | Description                                                                                                     |
|-------------------------------|--------------------------------------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------|
| setContext                    | context: object, id?: string                                 | void              | Sets the XComponent callback context and ID (optional). This API is called for video playback.                  |
| setDebug                      | open: boolean                                                | void              | Sets whether to enable device logs.                                                                             |
| native_setup                  | N/A                                                           | void              | Initializes the configuration.                                                                                  |
| setDataSource                 | url: string                                                  | void              | Sets the video source address.                                                                                  |
| setDataSourceHeader           | headers: Map<string, string>                                 | void              | Sets the HTTP request header of the video source.                                                               |
| setOption                     | category:string, key: string, value: string                  | void              | Sets preset char parameters before playback .                                                                   |
| setOptionLong                 | category:string, key: string, value: string                  | void              | Sets preset int parameters before playback.                                                                     |
| prepareAsync                  | N/A                                                           | void              | Loads videos.                                                                                                   |
| start                         | N/A                                                           | void              | Starts playback.                                                                                                |
| stop                          | N/A                                                           | void              | Stops playback.                                                                                                 |
| pause                         | N/A                                                           | void              | Pauses playback.                                                                                                |
| reset                         | N/A                                                           | void              | Resets playback.                                                                                                | 
| release                       | N/A                                                           | void              | Releases the resource.                                                                                          |
| seekTo                        | msec: string                                                | void              | Fast-forwards or rewinds playback.                                                                              |
| setScreenOnWhilePlaying       | on: boolean                                                  | void              | Sets the screen to be always on.                                                                                |
| setSpeed                      | speed: string                                                | void              | Sets the playback speed.                                                                                        |
| getSpeed                      | N/A                                                           | number            | Obtains the playback speed.                                                                                     |
| isPlaying                     | N/A                                                           | boolean           | Checks whether the video is playing.                                                                            |
| setOnVideoSizeChangedListener | listener: OnVideoSizeChangedListener                         | void              | Sets the callback listener for obtaining the video width and height.                                            |
| setOnPreparedListener         | listener: OnPreparedListener                                 | void              | Sets the callback listener for video readiness.                                                                 |
| setOnInfoListener             | listener: OnInfoListener                                     | void              | Sets the callback listener for each player status.                                                              |
| setOnErrorListener            | listener: OnErrorListener                                    | void              | Sets the callback listener for playback exceptions.                                                             |
| setOnBufferingUpdateListener  | listener: OnBufferingUpdateListener                          | void              | Sets the buffer callback listener.                                                                              |
| setOnSeekCompleteListener     | listener: OnSeekCompleteListener                             | void              | Sets the callback listener for fast-forward and rewind.                                                         |
| setMessageListener            | N/A                                                           | void              | Sets the video listener to the napi for receiving callbacks.                                                    |
| getVideoWidth                 | N/A                                                           | number            | Obtains the video width.                                                                                        |
| getVideoHeight                | N/A                                                           | number            | Obtains the video height.                                                                                       |
| getVideoSarNum                | N/A                                                           | number            | Obtain the numerator of the video's aspect ratio.                                                               |
| getVideoSarDen                | N/A                                                           | number            | Obtain the denominator of the video's aspect ratio.                                                             |
| getDuration                   | N/A                                                           | number            | Obtains the total video duration.                                                                               |
| getCurrentPosition            | N/A                                                           | number            | Obtains the current position of video playback.                                                                 |
| getAudioSessionId             | N/A                                                           | number            | Obtains the audio session ID.                                                                                   |
| setVolume                     | leftVolume: string,rightVolume:string                        | void              | Sets the volume.                                                                                                |
| setLoopCount                  | looping: boolean                                             | void              | Enables loop playback.                                                                                          |
| isLooping                     | N/A                                                           | boolean           | Check whether loop playback is enabled.                                                                         |
| selectTrack                   | track: string                                                | void              | Selects a track.                                                                                                |
| deselectTrack                 | track: string                                                | void              | Deletes the selected track.                                                                                     |
| getMediaInfo                  | N/A                                                           | object            | Obtains media stream information.                                                                               |
| setAudioId                    | id: string                                                   | void              | Sets the ID of the audio to be created.                                                                         |
| on                            | type: 'audioInterrupt', callback: Callback< InterruptEvent >| void              | Subscribes to audio interruption events. This API uses an asynchronous callback to return the result.           |
| on                            | type: 'deviceChange', callback: Callback< InterruptEvent >| void              | Subscribes to audio disconnect and connect events. This API uses an asynchronous callback to return the result. |
| off                           | type: 'audioInterrupt'                                      | void              | Unsubscribes from audio interruption events.                                                                    |
| off                           | type: 'deviceChange'                                      | void              | Unsubscribes from audio disconnect and connect events events.                                                   |
| startRecord                           | saveFilePath: string                                       | boolean              | Enable video recording                                                                                          |
| isRecord                           | N/A                                      | boolean              | Get recording status                                                                                            |
| stopRecord                           | N/A                                      | Promise<boolean>              | Stop video recording                                                                                            |
| screenshot                           | saveFilePath: string     | Promise<boolean>               | screenshot                                                                                                      |
| stopAsync                           | N/A                                                            | Promise<boolean>               | Stop playback the asynchronous method                                                                            |
| releaseAsync                           | N/A                                                            | Promise<boolean>               | Release resources the asynchronous method                                                                       |

### Parameter Description
1.	InterruptEvent
Describes the interruption event received by the application when playback is interrupted.

| Parameter     | Type              | Mandatory| Description                                |
|-----------|--------------------|------|--------------------------------------|
| forceType | InterruptForceType | Yes  | Whether the interruption is taken by the system or to be taken by the application.|
| hintType  | InterruptHint      | Yes  | Hint provided along the interruption.                          |

2.	InterruptForceType
Enumerates the types of force that causes audio interruption.

| Parameter           | Value| Description                                |
|-----------------|----|--------------------------------------|
| INTERRUPT_FORCE | 0  | Forced action taken by the system.  |
| INTERRUPT_SHARE | 1  | The application can choose to take action or ignore.|

3.	InterruptHint
Enumerates the hints provided along with audio interruption.

| Parameter                 | Value| Description                                        |
|-----------------------|----|----------------------------------------------|
| INTERRUPT_HINT_NONE   | 0  | None.                                    |
| INTERRUPT_HINT_RESUME | 1  | Resumes the playback.                              |
| INTERRUPT_HINT_PAUSE  | 2  | Pauses the playback.                              |
| INTERRUPT_HINT_STOP   | 3  | Stops the playback.                              |
| INTERRUPT_HINT_DUCK   | 4  | Ducks the playback. (In ducking, the audio volume is reduced, but not silenced.)|
| INTERRUPT_HINT_UNDUCK | 5  | Unducks the playback.                              |

## Notes
- State management is required for implementation,[Refer to the Demo](https://gitcode.com/openharmony-sig/ohos_ijkplayer/blob/master/entry/src/main/ets/pages/IjkplayerMapManager.ts)
- [Refer to the Navigation Example](https://gitcode.com/openharmony-sig/ohos_ijkplayer/blob/master/entry/src/main/ets/pages/IjkVideoPlayerNavigationExample.ets)
- [Refer to the Not Navigation Example](https://gitcode.com/openharmony-sig/ohos_ijkplayer/blob/master/entry/src/main/ets/pages/IjkVideoPlayerPage.ets)


## About obfuscation
- Code obfuscation, please see[Code Obfuscation](https://docs.openharmony.cn/pages/v5.0/zh-cn/application-dev/arkts-utils/source-obfuscation.md)
- If you want the ijkplayer library not to be obfuscated during code obfuscation, you need to add corresponding exclusion rules in the obfuscation rule configuration file obfuscation-rules.txt：
```
-keep
./oh_modules/@ohos/ijkplayer
```

## Constraints

This project has been verified in the following version:
- DevEco Studio: NEXT Beta1-5.0.3.806, SDK: API12 Release (5.0.0.66)
- DevEco Studio NEXT 5.0 (5.0.3.427) --SDK: API12

 To listen to audio interruption events, ensure that the device system version is 22 or later.
 To set the volume, ensure that the SDK version is 12 or later.

## Directory Structure

```javascript
|---- ijkplayer  
|     |---- entry  # Sample code
|     |---- ijkplayer  # ijkplayer libraries
|			|---- cpp  # Native modules
|                  |----- ijkplayer # ijkplayer internal service
|                  |----- ijksdl    # ijkplayer internal service
|                  |----- napi     # Encapsulated NAPIs
|                  |----- proxy     # Proxy for the NAPI to process ijkplayer internal services
|                  |----- third_party # Third-party library dependencies
|                  |----- utils     # Utils
|            |---- ets  # ets interface module
|                  |----- callback  # Video callback
|                  |----- common    # Constants
|                  |----- utils     # Utils 
|                  |----- IjkMediaPlayer.ets # napi calling APIs exposed by ijkplayer
|     |---- README.MD  # Readme                  
```

## How to Contribute

If you find any problem during the use, submit an [Issue](https://gitcode.com/openharmony-sig/ohos_ijkplayer/issues) or a [PR](https://gitcode.com/openharmony-sig/ohos_ijkplayer/pulls) to us.

## License

This project is based on [LGPLv2.1 or later](LICENSE).
