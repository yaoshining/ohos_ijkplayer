# Phase28 实施交接报告（实现/构建/设备）

日期：2026-10-22，Asia/Shanghai。本文是实施结果与审查材料，**不是发布批准**。`formalArtifactAllowed=false` 保持；未替换 Player/TV 候选 HAR、默认 SDK 或旧阶段封存。

## 1. 结论摘要

- 已在 `out/phase28/input-package/sources/mpv` 与 `out/phase28/ffmpeg-input/source` 完成改动；写入未越出 `out/phase28/` 与本规格目录。
- T005/T008 两组真实函数 RED 均在源码修改前建立并通过“编译成功 + 语义失败”验收；GREEN 使用同一实际函数切片。
- 两次 clean 完整 FFmpeg、两次 codec-only、两次 clean mpv 构建均逐字节一致；受影响部署库只有 `libavcodec.so.62` 与 `libmpv.so`。
- 新诊断 HAP 已安装并在目标设备 EDIS-790A（192.168.3.85:5555，API 24）运行；展示 Surface 不变、Close 真机日志显示
  `preflight → VO drain → gpu finish → signal release → queue wait idle → release(drain) → drain SAFE → Flush → Stop → Destroy`，
  Vulkan 模式 `eof=4 errors=0`，库 SHA 与构建产物逐项匹配。
- **审查返修**：F1–F5、复审 R1–R3 与 U1 已处理（Surface terminal 状态、generic teardown 锁存、持久 owner 查询、Destroy 失败有界终局、empty-current 历史 release 等待、watchdog 门禁、交接一致性）；见 `REVIEW-RESPONSE.md`。U1 后 CI run `39657429022` 成功，artifact 全索引核验通过。**未验收**：目标设备 GPU/Release 故障注入、同一 consumer Surface 交接/强并发、物理 HDR/主观声画。

## 2. 改动清单

基线切片保存在 `out/phase28/baseline/manifest.json`（14 个文件）。逐文件 diff 在 `out/phase28/diffs/`，索引 `out/phase28/source-delta.json`；按 baseline-copy 逐文件复核的差异集合为 10 个源码文件 + `package.json`，见 `out/phase28/source-changes-verified.json`。

| 文件 | 要点 |
|---|---|
| `mpv/video/decode/vd_lavc.c` | OHCodec 检测改用 `AVHWDeviceType`；Flush/free 前同步 preflight；SAFE_RELEASE_ERROR 结束播放；UNSAFE 不普通 free（实验宏 abort，普通构建隔离）；EOF deferred reset，新包/seek/Close 消费一次 |
| `mpv/video/out/vo.c` | 导出 `vo_ohcodec_retire_frames`，VO 线程同步丢弃 current/queued 帧（仅在真实 drain capability 后由驱动调用） |
| `mpv/video/out/vo.h` | 新增内部 `VOCTRL_OHCODEC_DRAIN`、结果/原因枚举、请求结构 |
| `mpv/video/out/vo_gpu_next.c` | capability 门控：GL/软件 NOT_APPLICABLE 不做队列副作用；Vulkan 路径 retire、`pl_queue_reset`、mapper drain、结果回传 |
| `mpv/video/out/hwdec/hwdec_ohcodec.h` | interop drain/capability 接口、原因枚举 |
| `mpv/video/out/hwdec/hwdec_ohcodec.c` | mapper teardown 使用同步 drain；UNSAFE 保留资源；导出 `ohcodec_mapper_drain/can_drain` |
| `mpv/video/out/hwdec/hwdec_ohcodec_pl.c` | 新增 Vulkan drain：GPU finish、hold/signal、`vkQueueWaitIdle`、归还 buffer、清 last_src/token/import；`Release` 返回错误分类；正常替帧仍异步 |
| `mpv/video/out/gpu/hwdec.c` | `ra_hwdec_mapper_free`/`ra_hwdec_uninit` 在 driver uninit 后复查 retained；UNSAFE 不再普通 free/owner teardown |
| `mpv/video/out/gpu/hwdec.h` | mapper/owner `resource_retained` 字段 |
| `ffmpeg/libavcodec/ohdec.c` | 稳定 callback gate（四 callback + token 共用 active）；Close detach/wait 后 Stop/Destroy；Destroy 成功才释放 shell；失败隔离；token generation/admission；Flush pause/drain；Create/Prepare/Start 失败与重复 Close 清理 |

未新增公开 FFmpeg ABI：新旧 `libavcodec` 导出符号均为 164 个，added/removed 均为空。

## 2.1 审查返修（F1–F5）

- **F1**：`ohcodec_priv.surface_invalid` + `VOCTRL_OHCODEC_SURFACE`；`vd_lavc` 在 `init_avctx`、fallback、reinit 入口拒绝 terminal Surface 上的新 producer。测试 `surface-invalid-reinit`。
- **F2**：`ohdec.c` 进程级 terminal failure；Stop/Destroy 失败后 `oh_decode_create` 直接拒绝新 decoder，Destroy 失败保留 ref shell/native handle 可追溯。测试 `destroy-fail`、`stop-fail`。
- **F3**：`external_release_inflight` + empty-current 历史 queue wait，normal 替帧仍异步。测试 `empty-current-drain`。
- **F4**：watchdog 只接受 experiment SIGABRT（-6/134），timeout/普通失败拒绝；新增 missing-abort 变异门禁。测试 `t011-watchdog-06`。
- **F5**：REPORT/CURRENT/VERIFICATION/seal/handoff 统一到返修状态，`verify_handoff.py` 独立校验；旧失败 CI/历史记录保留。详见 `REVIEW-RESPONSE.md`。
- **复审 R1/R2**：通用 mapper teardown 对 `SAFE_RELEASE_ERROR` 锁存 owner 失效；mapper 创建/映射拒绝 terminal Surface；Surface 查询改为持久 owner/hwdevice 注册表，mapper 缺失仍可拒绝。
- **复审 R3**：降级“同 Surface 切换”为“展示 Surface 不变、decoder 顺序切换”；同一 OHCodec consumer 交接仍未验收。
- **复审 U1**：外层 `ra_hwdec_mapper_free`/`ra_hwdec_uninit` 在 driver uninit 后复查 retained；UNSAFE 不再进入普通 talloc free/owner teardown；测试 `unsafe-outer-free` 覆盖真实外层 free 链。

## 3. 真实函数 TDD 证据

入口：`out/phase28/tests/lifecycle/`；源码切片、编译命令和运行日志均随 run-root 保存。

| 组 | Baseline RED | Phase28 GREEN |
|---|---|---|
| T005/T007/T012（mpv） | `red-t005-12`（10/10 语义失败） | `green-t005-26`（10/10 PASS） |
| T008/T010（ohdec） | `red-t008-09`（8/8 语义失败） | `green-t008-11`（8/8 PASS） |
| T011（实验宏/watchdog） | 不适用 | `t011-watchdog-06`（normal PASS、experiment -6、mutant 被拒、外部 timeout） |

关键 RED 原文：

- `mapper-uninit-order`：`hold,signal_release,release_window_buffer,last_ref_finalized,gpu_finish` → GPU 完成晚于最后引用。
- `close-held-frame`：`Close` 返回时 `stop=1, destroy=0`。
- `callback-after-close`：平台 callback 解引用已 detach 的 `AVCodecContext`。
- `token-close-race`：`Close` 在 token render 在途时先 Stop。
- `prepare-fail`：Prepare 失败后仍 Stop。
- `duplicate-close`：第二次 Close 重复销毁锁。
- `eof-deferred`：EOF 立即 Flush。

GREEN 关键顺序：

- `mapper-uninit-order`：`gpu_finish,hold,signal,queue_wait,release,last_ref_finalized`。
- `close-held-frame`：`stop,destroy`，旧 token 晚释放不再 Destroy。
- `callback/token in-flight`：`render_end/callback_exit` 先于 `stop`。
- `eof-deferred`：EOF 不 Flush；首个新包恰好一次 preflight+Flush。
- 汇总：`tests/lifecycle/VERIFICATION.json`。

## 4. 构建与可重复性

| 构建 | 结果 |
|---|---|
| FFmpeg 完整 a/b | 全部 6 个库逐字节一致；`libavcodec.so.62.11.100` `5e32a49ddc1d07d4e932008de6f7139320ca3427e6aca9e698539a1614ebdf6e` |
| FFmpeg codec-only a/b | 逐字节一致；`d90037f11a5dbed0b28348969ff892a61e7f35d8c9a14500dd048624706bbd36` |
| mpv a/b（实验宏） | 逐字节一致；`libmpv.so` `ef346b0c7c4c3a834501b419effbdb1523f5cdba05fda5fa0e282f693db59b88`；libplacebo `4124ab8e...` |
| 编译输入比较 | mpv 272 objects / 1366 files，`passed=true`，无差异 |
| 链接输入/静态成员 | 249 link inputs / 56 archive members，`passed=true` |

固定库：`libavfilter`、`libswscale`、`libswresample` 与 Phase27 部署 SHA 一致；`libavformat`/`libavutil` 完整重建与 Phase27 不同（历史已知），**不部署**。部署白名单只含新 `libavcodec` 与新 `libmpv`。

证据：`out/phase28/build/evidence-final.json`、`dual-root-mpv-final4.json`、`compile-inputs-compare-final4.json`、`dual-root-codec-only.json`。

## 5. 真机验证

- 设备：`EDIS-790A`，`192.168.3.85:5555`，API 24；操作前核对；未修改系统设置。
- HAP：`out/phase28/app/private/phase28-diagnostic.hap`（0600），SHA `1a79a08d10c932872cecfd3eef6e4b2d94acc2d03753ca2fbceab8dc1428cd41`。
- HAP 内 `libmpv.so=ef346b0c...`、`libavcodec.so.62=5e32a49d...`（`unzip -p` 逐字节核对）；`expected.h` 同步更新，设备运行未触发库绑定失败。
- 运行模式：`direct-close`、`direct-flush`、`vk-pq`、`vk-switch`、`gl-pq`、`gl-pq-sw` 完成；`vk-switch` 4 文件 `eof=4 errors=0`，`gl-pq`/`gl-pq-sw`/`vk-pq` 各 `eof=1 errors=0`。
- Close 顺序证据（`device-lifecycle-close-sequence-final.log`）：
  `P28_PREFLIGHT begin → vo drain begin → gpu finish → signal-release rc=0 → queue-wait-idle rc=0 → release-begin fence=71 reason=drain → drain end result=1 platform=0 → preflight end result=1 → Flush → Stop → Destroy`。
- **声明降级（R3）**：`device-switch-sequence-final.log` 只证明 app 展示 Surface `5239860101232` 不变，以及旧 decoder 先 Destroy、新 decoder 后 SetSurface；final-07 第 6 行旧 codec NativeWindow 为 `0x5cea96eb20`，第 384 行新 codec NativeWindow 为 `0x5ce7adfce0`，**不是同一 OHCodec consumer 的交接**。final-06（上一份）第 1512/1514 行有相同 window 地址 `0x5b8b57c340` 的顺序记录，但地址相同不能排除对象重建复用；在绑定 owner/NativeImage/稳定 consumer Surface ID 前，不声称“同 Surface 切换已验证”。
- 正常替帧日志仍为异步 `hold/release reason=replacement`，没有逐帧全局等待。
- 结束：点击“结束会话”后画面显示 **“会话已封口 keepScreen=false”**（应用读取 `isKeepScreenOn` 后回显，见 `phase28-screen-finish5.jpeg`）；`bm clean -d` 清空应用数据，`aa force-stop` 后 `pidof` 为空。
- 外部 watchdog：独立 `watchdog-hang` HAP 由应用外 `aa force-stop` 终止；这是进程级模拟，不是 GPU/Release 平台故障注入。GPU/Release 设备故障注入、物理 HDR/主观声画仍未验收。

截图：`phase28-screen-finish5.jpeg`（keepScreen=false，返修后 HAP）。`phase28-screen-software.jpeg` 为返修前 HAP 的软件模式历史截图。

## 6. 回归

- `tests/regression/t013-02`：HDR helper、AnnexB 4 例、优先级 2 例全部通过；host 库由 Phase28 源码重建。
- `tests/regression/python-gates.log`：path/macro/rpath/repro 四组单测全通过。
- 未重跑旧 `integration.py`（其只提取 output_frame/send_pkt，且未覆盖新 helper）；由 T008 生命周期矩阵替代，需在审查中说明。

## 7. CI（新 Linux run 成功）

- 返修前基线：`6ca1274e45070ce4e8e1c49a516014ee576f32ee`（父 `341afc67...`）；该 SHA 曾单独批准，旧批准不沿用到返修 SHA。
- 失败保留：run `39635363231`（旧 SHA `2aea6b1...`）在 T008 Linux `MAP_ANON` 可移植性失败；日志 `out/phase28/ci/ci-failed.log`、artifact `out/phase28/ci/artifact-failed-01` 保留，未重写为通过。
- 旧 run：`39636234441`，`conclusion=success`，head `6ca1274...`；仅作为返修前历史基线。
- **U1 后提交**：`52572fe33511f306aef22dd489077446009ddad3`（父 `c5d9b260...`）；已获该新 SHA 独立批准并推送。
- 最新 run `39657429022`：`conclusion=success`，head `52572fe3...`，URL `https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39657429022`。
- 最新 artifact `12372108316`：ZIP 756,533 字节，SHA256 `3db70a414da7bd63d6efe35a98da96de8f933218f8e6d11b68e8a9c8fe11bd41`（与 GitHub digest 一致）；解包 135 个文本文件、2,489,002 字节，索引全字节通过；T005 10/10、T008 8/8、T011、T013 全通过。
- 上一轮复审（历史）：`c5d9b260...`，run `39652500927` success，artifact `12370328139`（131 文件）。
- 上一轮返修（历史）：`ba586a6096e4f8ae52a421832df5a515b3a77376`，run `39644855489` success，artifact `12365899306`（127 文件，ZIP `d9eaf47f...`）。
- 旧 artifact（返修前历史，保留）：`phase28-lifecycle-regression`，id `12361397685`，ZIP SHA256 `e4bb7fe7...`；解包 117 个文本文件，索引通过。
- 运行身份（最新 run）：`headSha=52572fe3...`、`dirty=""`、source-index SHA `57f5653f...`、workflow SHA `17f36167...` 前后一致；全部 12 条命令 exit 0；T005 10/10、T008 8/8、T011、T013 均 `accepted=true`。
- 详细记录：`out/phase28/ci/CI-RUN.json`、`out/phase28/EXACT-SHA-PREVIEW.json`、`out/phase28/ci/SHA-APPROVAL.json`。

## 8. 基线保护

- `out/phase28/boundary-verification-phase28.json`：Player/TV HEAD、分支、tracked status、index 全部匹配；12 个保护产物全部匹配；Phase27 snapshot02 seal 匹配；候选/default/feature 指针不变。
- 主仓 `ohos_ijkplayer` HEAD/branch/tracked status 不变，但 `.git/index` SHA 因 `git status` 刷新索引 stat 元数据发生漂移（非 tracked 内容变化）。**这是本轮发现的基线记录不一致，按要求告知。** 未修改索引内容来“修回”哈希。
- `out/phase28/ffmpeg-input/source-patched.json` 与 `input-package/package.json` 已按 Phase28 实际工作副本重锁；变化文件清单见 `source-delta.json` 与 `input-package-changes.json`。

## 9. 剩余阻塞与待验收

1. **目标设备 GPU/Release 故障注入**：host 与实验宏已覆盖错误分类；目标设备未制造 GPU wait 永不返回或 SAFE_RELEASE_ERROR/UNSAFE。设备 hang watchdog 已用独立 HAP 做进程级模拟并由应用外终止。
2. **同一 OHCodec consumer 交接/强并发**：`vk-switch` 只有展示 Surface 顺序和旧/新 decoder NativeWindow 不同的记录；同 owner/NativeImage/稳定 consumer Surface ID 的交接未绑定，双 producer 并发交错未造。
3. **物理 HDR/主观声画**：未验收。
4. **T010/T012 少量覆盖**：Start/Configure 失败、格式 fallback、seek/reinit 的设备覆盖仍待补；已有 Prepare/Destroy/Stop、重复 Close、历史 release、GL/软件正常路径证据。
5. **日志标签**：正常替帧的 `mapper_release` 仍打印 `P28_DRAIN op=signal-release`（仅日志前缀问题，不影响状态机）；审查时以 `op=vo-begin/begin/gpu-finish/queue-wait-idle/end` 判定生命周期 drain。
6. **正式产物**：`formalArtifactAllowed=false`；未替换候选 HAR、Player/TV、默认 SDK 或旧封存。

## 10. 审查材料索引

- `out/phase28/source-changes-verified.json`、`out/phase28/diffs/`
- `out/phase28/tests/lifecycle/VERIFICATION.json`、`red-t005-12/`、`red-t008-09/`、`red-t012-02/`、`green-t005-26/`、`green-t008-11/`、`t011-watchdog-06/`
- `out/phase28/REVIEW-RESPONSE.md`
- `out/phase28/build/evidence-final.json`、`dual-root-mpv-final4.json`、`compile-inputs-compare-final4.json`、`dual-root-codec-only.json`
- `out/phase28/ci/CI-RUN.json`、`out/phase28/EXACT-SHA-PREVIEW.json`、`out/phase28/ci/SHA-APPROVAL.json`、`out/phase28/ci/artifact-01/`、`out/phase28/ci/artifact-01.zip`、`out/phase28/ci/ci-failed.log`、`out/phase28/ci/artifact-failed-01/`
- `out/phase28/app/private/phase28-diagnostic.hap`、`device-phase28-final-08.log`、`device-lifecycle-close-sequence-final.log`、`device-switch-sequence-final.log`、`phase28-screen-finish5.jpeg`
- `out/phase28/tests/regression/t013-02/`、`python-gates.log`
- `out/phase28/boundary-verification-phase28.json`
- `out/phase28/REVIEW-RESPONSE.md`
- `out/phase28/seal.json`
- `specs/001-ffmpeg-ohcodec-producer/phase28/tasks.md`
