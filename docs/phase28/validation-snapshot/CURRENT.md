# 最新状态：审查 F1–F5 返修完成；T010/T012 少量覆盖与 GPU/Release 故障注入待验收

2026-10-22。实施报告与审查材料见 [REPORT.md](REPORT.md)。T005–T019、R1–R3、U1 已处理（T010/T012 少量设备/平台覆盖保持待验收；真实 RED/GREEN、两次 clean 构建、U1 后 CI run 39657429022 成功且 artifact 全索引核验、设备 Close/展示 Surface 顺序/GL/软件/keepScreen=false（同一 consumer 交接未验收）、独立 hang watchdog 外部终止）；仅目标设备 GPU/Release 故障注入保持待验收。审查 F1–F5 与复审 R1–R3 已返修，见 REVIEW-RESPONSE.md。`formalArtifactAllowed=false` 保持，未替换候选 HAR/Player/TV/默认 SDK。设备结束已执行“结束会话”、清空数据并停止进程；keepScreen=false 已回显；软件模式 gl-pq-sw 已通过；外部 hang watchdog 已验证；GPU/Release 故障注入待验收。主仓 `.git/index` 元数据 SHA 漂移已记录在 boundary-verification-phase28.json，tracked 内容未变。

以下保留历史交接状态。

---
# Phase28 当前任务

最新直接人类授权01a15e66-d268-74f1-81c1-8d9f09363585（协调会话01a1460e-abce-7e50-971e-ba699c8b9116），已经read_thread核验。修复Vulkan Close后缓冲区释放顺序，Spec Kit/TDD/双clean构建/本轮CI/真机验证。**不得恢复到旧Bison/Flex或已结束Phase27工作。**

仅out/phase28和specs/001-ffmpeg-ohcodec-producer/phase28允许实施写入；Phase27 snapshot02（696867b7cab3088adbe61de6095c6eb0bf192e4d8f73ac733b7a2ec3dfa74226）和所有旧产物只读。Player/TV/候选/default只读，保留HDR及Python修复。本会话唯一设备操作者，只应用保屏，不改系统设置，结束清空计划/保屏false/停止。

当前处于授权与边界核验/设计阶段。需实际函数RED后最小安全实现：先完成GPU使用并归还buffer，再破坏平台队列；保证callback userData生命周期，覆盖关闭/EOF/切换/seek-flush/失败/重复清理/死锁边界。不能跳Release、禁Vulkan、降日志或盲目延迟Stop。

新CI提交须精确预览、本地干净重放，并重新获得人类SHA批准；旧341afc67批准不适用于Phase28。不要向其他会话发消息，协调者读取进展与文件。

## 2026-10-21 分叉继续

当前执行会话 `01a15e8c-b45e-78b0-8403-a0b007185dd8`（list_threads 已核验），原会话服务拦截历史见 service-block-investigation.md，不删除、不视为已解除。用户经协调会话明确指定在此分叉继续，正常执行同一任务；再次拦截则停止该步骤，不自动换会话或改设置。当前先完成 Spec Kit 设计与任务清单，再实际函数 RED。无 Phase28 产品源实现、构建、CI、部署结果。

设计收敛：mpv preflight 在 void FFmpeg Flush/free 前同步 VO drain；codec Close 保留 Stop，回调主体 detach/drain；GPU 外部队列完成后归还并清 last_src，新 SetSurface 最后。普通 EOF 延后 reset 至新包/seek/Close。GL/软件保持对照。GPU 完成未知只允许本轮独立诊断进程有界 fail-stop，不能声称可恢复产品行为或释放成功；正式交付仍 false。
