# Phase30 A 关闭错误后的会话恢复

## 用户需求

分别注入 FFmpeg OHCodec 的 Stop 和 Destroy 错误，核对旧回调、token、buffer 和 Surface 的归属。安全保留无法确认销毁的旧资源后，用户更换视频和 Surface，须能在同一 PID 恢复硬解并有画面和声音。

2026-11-10 用户追加要求继续云调试，最终完整修复问题。此文记录本次正式构建交接前的要求。首轮候选补丁和宿主测试已在本文建立前完成，其时间顺序沿用实际记录。

## 验收要求

- 原版分别复现两种错误导致新建在平台调用前返回 AVERROR_EXTERNAL。
- 关闭先使 token generation 失效，detach 回调，等待 active 操作完成。
- 旧 token 的迟到 render 返回 ESTALE，discard 不操作任何新实例的 buffer。
- Destroy 成功时可释放旧生产者的占用，即使此前 Stop 失败。
- Destroy 失败时保留旧回调壳、锁、句柄及生产侧窗口引用。旧 Surface ID 持续被拒绝复用，新 Surface 的独立实例可以启动。
- 同一个 Surface 的不同 NativeWindow wrapper 仍视为同一消费者。
- Stop、Destroy 两轮真机分别记录同一 PID 的 A 和 B，B 的 Surface ID 不同，B 为硬解，具有变化的画面与音频输出。
- 正常构建入口自动应用修复，并产生可核对源码和库摘要的 SDK。诊断注入只存在于独立测试库。
- Player、TV 源仓职责维持生产者与消费者分工，交付包含修复源与生产库，不修改历史封存。

## 边界

验证针对返回错误，未要求解决平台调用永久不返回。无法确认销毁的资源保留到进程退出，平台资源耗尽仍可能使后续创建失败。候选不承诺无限次数的失败恢复。

## 用户故事与可测要求（2026-11-10 补全）

### US1 / P1：关闭失败后继续播放另一部视频

给定 A 已绑定 Surface 并开始播放，分别让 Stop 或 Destroy 返回错误，关闭 A 后在同一 PID 为 B 创建不同 Surface。B 必须进入平台创建路径、硬解输出变化的画面与音频；退出 B 后列表仍可用。单独验证两种错误，不能使用 Vulkan 等待错误替代。

### US2 / P1：隔离旧实例资源

给定旧实例已关闭，即使旧 token 最后释放或旧回调晚到，也不能访问已经回收的上下文或操作 B 的 buffer。Destroy 失败时同 Surface 的另一 wrapper 必须在 SetSurface 前被拒绝；Destroy 成功时允许复用旧 Surface。

### US3 / P2：从合并后的来源交付正常 SDK

维护者可从固定 Phase30 A 全量源、静态依赖和 OpenHarmony SDK 执行构建入口。交付六库不含故障注入，来源、测试、真机证据可追踪；本次仅在 PR 检查完成并合并 `master` 后确认最终交付，不修改 Player/TV。

| 编号 | 要求 | 验收方式 |
| --- | --- | --- |
| FR-001 | 移除关闭错误导致的全进程拒绝创建；两种错误分别验证 | 原版 Create=1；候选 Create=2，B 创建成功 |
| FR-002 | 关闭先撤销回调准入、清空 attached、等待 active 并使 generation 失效 | 并发与迟到回调宿主断言，ASan/UBSan |
| FR-003 | 旧 token 的 render 返回 ESTALE，discard 不操作新/旧失效 index | token 关闭竞态及旧帧持有断言 |
| FR-004 | Destroy 成功释放窗口引用和 Surface 占用，即使 Stop 失败 | Stop 注入后 Surface 可复用，Destroy 不重复调用 |
| FR-005 | Destroy 失败保留旧壳、锁、句柄、窗口引用和 Surface ID，占用到 PID 退出 | 四类迟到回调、别名拒绝、新 Surface 可建 |
| FR-006 | SetSurface 前按 Surface ID 注册，拥有独立 NativeWindow 引用 | 同 ID 不同 wrapper 的冲突断言；引用计数断言 |
| FR-007 | Stop、Destroy 两轮分别证明同 PID、新 Surface、硬解音画恢复 | API 24 真机日志与截图；音频为设备输出幅度测量 |
| FR-008 | 正常入口校验全量来源、应用唯一修复、生成无注入六库及可核对清单 | build.py、inputs.lock.json、三根六库摘要比较 |
| FR-009 | 不覆盖历史封存，不修改消费者，明确局限与实际构建来源 | 隔离提交范围审计；buildOrigin=local |
| FR-010 | Spec Kit 工件完整、任务可追踪、CI/评审通过后合并默认分支再交付 | prerequisite、analysis、convergence、PR/merge 与交付绑定 |

## 成功标准

- SC-001：原版与候选各 8 项宿主用例完成；候选两类错误均恢复创建，6 项生命周期回归无 sanitizer 报错。
- SC-002：Stop PID 59523、Destroy PID 63191 的 B 三个采样窗口均 hw=active，Surface 与 A 不同，有连续变化画面和非零设备音频输出；列表仍可操作。
- SC-003：正常六库三根构建逐字节相同，217 个 SDK 清单文件可验证；无注入包 PID 12571 连播 A/B 硬解音画正常。
- SC-004：PR 精确提交通过新增恢复回归及仓库要求的检查，无未解决阻塞评审；合并提交含 SDK 对应补丁与构建输入，交付记录绑定实际合并 SHA。

## 澄清与非目标

用户已明确仅交付 FFmpeg SDK。2026-11-10 追加授权包含推送、PR 与主分支合并；不再把本地提交视为交付完成。不重新设计 mpv/Vulkan、不开启 Player/TV 接入，不承诺全部设备与无限次恢复。所有实际设备结果均来自返回错误注入；缺少真实平台随机故障的概率性覆盖不能被隐去。
