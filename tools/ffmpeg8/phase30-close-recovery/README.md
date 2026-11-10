# Phase30 A 解码器关闭故障复验

2026-11-10。候选补丁基于 Phase30 A 的 `libavcodec/ohdec.c`，原文件 SHA-256 为 `d7c4bcc960d54dcae930168a56fcd6cf2b064e8758294b9e6a98c80768f19499`。本地重新构建 arm64 FFmpeg。两种错误后更换视频和 Surface 的同 PID 硬解、动态画面及音频输出已通过 API 24 MatePad Air 真机验收。既有平板 Vulkan 等待注入覆盖另一条错误路径。

## 原版与候选

用同一套宿主平台替身分别向 Stop、Destroy 返回错误。每个用例先创建 A，再在同一进程中为 B 指定不同的 Surface。两次原版测试都在第二次 `oh_decode_create` 返回 `AVERROR_EXTERNAL`，平台 Create 计数均为 1。候选两次计数均为 2，新 token 使用新解码器执行 render。

| 归属 | Stop 失败，Destroy 成功 | Stop 成功，Destroy 失败 |
| --- | --- | --- |
| 回调 | 关闭前撤销准入、清空 attached，等 active 归零。Destroy 成功后允许释放回调壳。 | 保留已经 detach 的壳和锁。宿主释放旧上下文及最后一个旧 token 后，又调用四种旧回调，新队列和错误状态均未被改写。 |
| token 与 buffer | 旧 token 持有旧壳及旧 generation。迟到的 render 返回 ESTALE，discard 不调用平台 Free。销毁 FFmpeg 的队列容器。 | 同样使旧 token 失效。Stop 成功时平台释放解码器的输入输出缓冲。FFmpeg 队列项中的指针和索引是借用值，未交给新解码器。对失败的 Destroy 不再尝试原生操作。 |
| Surface | 以 Surface ID 预留生产者，持有独立 NativeWindow 引用。Destroy 成功后解除预留、归还该引用，允许复用此 ID。 | 旧解码器句柄按不可再使用处理，保留壳和旧 NativeWindow 引用及 ID 预留。不同 wrapper 若指向该 ID，在 SetSurface 前被拒绝。新 ID 可以独立申请。 |

mpv 拥有 NativeImage 和消费侧监听器。FFmpeg 单独持有生产侧 NativeWindow 的引用，不能通过保留 `hw_device_ctx` 中的裸指针延长 mpv 对象的生命周期。对 Destroy 返回错误，候选保守地将旧壳及预留保留至进程退出。连续发生此类错误会累积保留资源，最终能创建多少新硬件实例取决于设备容量。本次未做资源耗尽测试。

## 模拟器实测

两个诊断库分别在第一个已启动且已绑定窗口的实例上跳过一次指定平台调用，返回 `AV_ERR_UNKNOWN`（6）。另一项调用及随后 B 的全部调用照常执行。这样在 Destroy 注入时，旧原生实例确实尚未被主动销毁。两份诊断库均可重放得到相同的 SHA-256。

API 22 平板在应用进程内查询 H.264 硬件能力返回空，因此原生探针显式使用平台软件解码器 `OH.Media.Codec.Decoder.Video.AVC`。每轮均播放两份不同的 H.264 MP4，A 跨关闭持有一个真实 AVFrame；关闭后销毁 A 的消费侧 NativeImage。B 在新的 NativeImage 上启动后尝试渲染 A 的旧 token，再获取和归还 B 的输出缓冲。

| 注入 | 同轮 PID | A → B 的 Surface ID | A 的 Stop / Destroy | B 的实际结果 |
| --- | ---: | --- | --- | --- |
| Stop | 10348 | 44444321579008 → 44444321579009 | 注入 6 / 真实 0 | SetSurface 成功，旧 render 返回 -116，新 Surface 获取并归还 4 帧 |
| Destroy | 11020 | 47330539601920 → 47330539601921 | 真实 0 / 注入 6 | SetSurface 成功，旧 render 返回 -116，新 Surface 获取并归还 4 帧 |

B 的 4 个帧 PTS 均为 0、1024、2048、3072。B 正常 Stop 和 Destroy 都返回 0。模拟器应用是离屏 NativeImage 探针，未测音频。其启动器的 UI 检查将诊断页判为纯色，逐帧结果来自应用内的 NativeImage 和 HiLog。独立诊断进程已停止。

以下文件保存在本地，未提交到仓库：

- 宿主重放记录：`out/phase30-close-recovery/host-final.log`
- 定向 HiLog：`out/phase30-close-recovery/emulator-hilog.txt`
- Stop 逐帧记录：`out/phase30-close-recovery/emulator-stop.txt`
- Destroy 逐帧记录：`out/phase30-close-recovery/emulator-destroy.txt`

## 重放与真机验收

在仓库根目录运行 `python3 -B tools/ffmpeg8/phase30-close-recovery/test_recovery.py`。脚本校验 tests/baseline-ohdec.c 的原文件摘要，在临时目录应用 `recover.patch`，并分别编译原版和候选的实际函数。每版运行两项错误用例和六项已有生命周期用例，开启 AddressSanitizer 和 UndefinedBehaviorSanitizer。故意保留的资源不作泄漏检测。

诊断包构建使用 Phase30 A 的 TRACE 配置及 SDK。在完整构建的候选目录上运行 `python3 tools/ffmpeg8/phase30-close-recovery/build_probes.py BUILD NEW_OUTPUT`，生成 Stop 和 Destroy 专用库。正常候选不包含注入。两份离线播放页 HAP 均已签名，逐项核对本地 CI HAR 的九个原生库，只有 libavcodec 被替换。包名为 `com.yao.vidalltv`，用于隔离测试设备。

| 诊断 HAP（本地文件，未提交） | HAP SHA-256 |
| --- | --- |
| `out/phase30-close-recovery/stop/close-probe.hap` | `b11a7e700f265c280287795421d31d27a12b5960d5c39470fab1aacc5f028411` |
| `out/phase30-close-recovery/destroy/close-probe.hap` | `4d8a433dcf245d4dc652aa70bb6e9c738b84610db3babb922a87d08043464364` |

真机每包冷启动一次。在应用内先播 A，退回列表，再播 B。核对 CloseVerify 中 A 的指定调用 skipped=1、另一项返回值，以及 B 在同 PID、不同 Surface ID 上 SetSurface 成功。记录 B 的 hw=active、两帧可辨认且内容不同的屏幕画面、推进的播放位置与该音轨的非零输出幅度。遇到软件回退应单独记录。真机验收结果见下方，历史电视未用于本次验证。

## 2026-11-10 云真机验收

华为云调试 MatePad Air WKI-W10，HarmonyOS 6.1.0.112，API 24。使用上表逐字节核验过的两个诊断 HAP。同一轮内 A 退出、B 打开和关闭均在同一 PID，播放器及渲染器沿用生产 HAR 的八个库，只有 FFmpeg 使用独立注入库。

| 故障 | PID | A → B 的 Surface ID | B 播放进度 | B 非零音频样本 |
| --- | --- | --- | --- | --- |
| Stop 返回 6，Destroy 返回 0 | 59523 | 255649338359808 → 255649338359809 | 0 → 4333 ms | 95/96，峰值 0.0198 |
| Stop 返回 0，Destroy 返回 6 | 63191 | 271403278401536 → 271403278401537 | 0 → 4417 ms | 94/96，峰值 0.0182 |

两轮 B 的三个采样窗口均报告 hw=active、fmt=nv12、renderer=vulkan。Stop 场景截图中 B 的时间码从 00:00:00.750 到 00:00:03.000，Destroy 场景从 00:00:00.917 到 00:00:03.333，图案同步变化。两轮 B 正常 Stop/Destroy 均返回 0，关闭 7 秒后列表回报可用。

音频证据来自目标输出设备的 getMaxAmplitudeForOutputDevice，每窗 32 个样本、间隔 50 ms，联合播放进度及播放器状态判断。此次结论覆盖两条指定返回错误路径。平台调用永久不返回和资源耗尽没有纳入本次验收。

首个云会话在文件上传控件卡住后到期。第二个会话完成两种错误验证并已释放，控制台返回机型列表，剩余免费额度 306 分钟。第一次 Stop 播放的开始日志曾被系统噪声挤出日志窗口，因此在同一设备重新安装该包，以 PID 59523 的完整复验记录作为验收依据。

[Stop 完整定向记录](evidence/stop-accepted.txt)、[Destroy 完整定向记录](evidence/destroy-accepted.txt)、[结构化验收](evidence/verified.json)。原始连续截图保存在本地 out/phase30-close-recovery/cloud。

## 正常构建入口

本目录 build.py 是恢复版生产者入口。输入为固定的 9921 个 Phase30 A 源文件、固定静态 SMB/TLS sysroot 和 OpenHarmony native SDK。它在新的输出目录自动应用修复，核对补丁后 ohdec.c 摘要，构建六个共享库及头文件/pkgconfig，附带输入清单与许可。生成的正常库关闭 TRACE、TEST、DIAGNOSTIC 和 EXPERIMENT 宏。

```sh
python3 -B tools/ffmpeg8/phase30-close-recovery/build.py \
  --source out/phase30-consumer-handoff/target-sources/A/ffmpeg \
  --dependencies out/phase20/local-v3/origin-a/dependencies/sysroot \
  --ndk /Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native \
  --output out/phase30-close-recovery/new-normal-build
```

验收用 TRACE 注入库和正常 SDK 共享相同的补丁后 ohdec.c SHA-256，注入脚本只改独立副本。宿主回归默认关闭上述宏。正常 SDK 的 manifest 标明 buildOrigin=local，实际构建命令及全量输入摘要随 SDK 交付。Player 消费该生产者交接包时仍须更新自己的库锁与 HAR，消费者源仓在本任务中保持只读。


## 正常 SDK 回归与交付状态

三个独立构建根 normal-a、normal-b、normal-final 的六库 SHA-256 全部一致。正常 libavcodec 导出 164 个符号，与诊断包及旧版集合一致。正常库不包含 CloseVerify、P30 trace 或旧进程拒绝字符串。最终 SDK 的 217 个清单文件逐项校验通过。

最终无注入验收包 SHA-256 为 `db6c0771337e3824a8079dbe634c27fc433d1dfbfc3bddb58888cf1ef0458129`。包内六个 FFmpeg 库与 normal-final SDK 逐字节一致，其他三个 HAR 库与原 CI HAR 一致。API 24 MatePad Air 上，PID 12571 连续播放 A 和 B，六个采样窗口均为硬解 nv12/Vulkan，有变化的画面与音频输出，A/B 关闭 7 秒后列表均可操作。最终云会话已释放，免费额度余额为 303 分钟。

[正常库验收日志](evidence/normal-accepted.txt)、[三根构建比较](evidence/rebuild.json)、[正常 HAP 库绑定](evidence/normal-hap-binding.json)。本地 SDK 位于 out/phase30-close-recovery/normal-final/sdk，供消费者更新固定输入；本次库来源为本地构建。
