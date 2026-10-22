# NativeImage / FFmpeg 回调与 global/log/config 依赖审计

范围：`input-package-parentfix/sources/mpv` 与未修改的 `ffmpeg-input/source`。只读审计；未修改 Player/TV。

## NativeImage 回调

- `video/out/hwdec/hwdec_ohcodec.c:57 on_frame_available()`：只做 `surface->lock`、`pending++`、`cond_signal`；源码注释明确“NativeImage APIs are deliberately not called from this callback”。
- 监听器在 `ohcodec_surface_init()` 安装；`ohcodec_surface_destroy()`（`:101`）在 `hwdec_ohcodec_pl.c:834 owner_uninit()` 中调用，位置是 `ohcodec_surface_destroy`、`OH_NativeImage_Destroy`、`talloc_free(v)`。
- `owner_uninit` 只经 `ra_hwdec_uninit` → `hwdec_ohcodec.c:178 uninit()` 到达；UNSAFE 时 `resource_retained` 跳过 owner uninit，或屏障在 drain 内直接停住 VO 线程，`owner_uninit` 不可达。因此 Surface、listener、lock/cond 与 pending 计数均保留，晚到 callback 仍只访问保留对象。
- 宿主测试 `green-parentfix-e/callback-retained` 提取真实 `on_frame_available`，在 retained surface 上连续回调两次，`pending=2`，无 NativeImage API 调用。
- 锁：callback 只取 surface 锁；`ohcodec_mapper_drain` 不持有 surface 锁；barrier 不持有 GPU/queue/surface 锁。

## FFmpeg OHCodec 回调

- `ffmpeg-input/source/libavcodec/ohdec.c`：`oh_decode_on_err`（:530）与 `oh_decode_on_output`（:689）先 `oh_decode_admit()`（:168），在 gate 锁内检查 `detached/paused/attached` 并增加 active，再 `oh_decode_end()`（:182）减少并广播。
- `oh_decode_close`（:823）在 gate 下 detach，等待 active==0，不持 queue 锁或平台 callback mutex；token/frame 引用在 close 后仍可安全释放。
- mpv 侧 `vd_lavc.c uninit_avctx` 在 UNSAFE 时只 quarantine `AVCodecContext`，不调用 `avcodec_free_context`；preflight 屏障使 `vo_control` 不返回，`uninit_avctx` 后续清理不可达。SAFE/正常路径仍 free。
- 本轮按同一 harness 重放 8 例：`resume-04/parentfix/ffmpeg-regression-normal/results.json` 与 `ffmpeg-regression-diagnostic/results.json` 均为 8/8 ACCEPTED（close-held-frame、callback-after-close、token-close-race、callback-inflight-close、prepare/stop/destroy fail、duplicate close）。FFmpeg 源本轮未改，这是对未变依赖的新鲜重放，不是新真机改动。

## global / log / input / osd / config / mpctx

- 真实 `player/main.c mp_destroy()` 顺序：`mp_shutdown_clients` → `mp_uninit_ipc` → `uninit_audio_out` → `uninit_video_out`（`uninit_video_chain` → `vo_destroy`）→ encoder → `command_uninit` → clients → `osd_free` → terminal → `mp_input_uninit` → clipboard → `uninit_libav` → `mp_msg_uninit` → `talloc_free(abort_list)` → `talloc_free(mconfig)` → `talloc_free(mpctx)`。
- `player/video.c uninit_video_out()` 的真实 `vo_destroy()` 是屏障所在；`mp_destroy` 在它返回前不会继续释放 global/log/input/osd/config/mpctx。
- 宿主 `green-parentfix-e` 的 `EVENT parent_counts` 在 barrier 用例中这些计数全为 0；normal 用例全为 1。late 路径按真实 `mp_destroy` 次序可能先执行 `mp_uninit_ipc`/`uninit_audio_out`/`uninit_video_chain`，但屏障后核心父级与 mpctx 不再释放；preflight 路径连这些前置清理也不可达。
- 外部依赖（`mp_msg_uninit`、`uninit_libav`、`uninit_audio_out` 等）在宿主中是带计数的测试替身；真实顺序、调用点和 `vo_destroy`/`mp_destroy` 切片是源码提取，未改写。

## 边界

- 本审计不等同于真实硬件故障注入；未覆盖真实 GPU 永不返回、真实强并发、物理 HDR/主观声画。
- normal 构建不编译屏障/晚到预检；normal 真实 UNSAFE 产品策略仍为 pending。

## F1 零销毁门禁返修

- 每个关键销毁入口（queue/registry/GPU/renderer/options/cache/icc/lut/shader/texture/avctx/mapper/owner/vk-mapper/parent-*/uninit-end/dr_helper）现在立即输出 `EVENT ...` 并增加 `c_destroy_events`；事件在锁内刷新。
- 屏障/abort 期间启动观察线程，每 100ms 输出 `EVENT observer-snapshot destroy_events=...` 及关键计数；不再依赖 core 正常结束后的最终计数。
- `run.py` 对 preflight/experiment 要求零禁止事件；对 late 仅允许真实 `mp_destroy` 先行的 ipc/audio/video-chain/uninit-begin，仍拒绝任何关键销毁事件。
- 新增 F1 负例：把真实 `vo_gpu_next.uninit` 的既有 `pl_queue_destroy` 移到 drain 前；`late-unsafe` 日志出现 `EVENT destroy-queue`，测试将其判为负例拒绝（不再 accepted）。
