# Phase28 规格与验证快照

本次仅补交中文规格和既有验证文本；实现与测试已提交于 `52572fe33511f306aef22dd489077446009ddad3`，历史 CI run `39657429022` 验证该代码提交。此文档提交没有新的 CI 或设备验收，不继承为新 SHA 的绿灯。`formalArtifactAllowed=false`。

- 规格快照：`specs/001-ffmpeg-ohcodec-producer/phase28/`，保留设计与执行记录的原文。
- 实施结果：[REPORT.md](validation-snapshot/REPORT.md)、[REVIEW-RESPONSE.md](validation-snapshot/REVIEW-RESPONSE.md)。
- 最终独立复审：[INDEPENDENT-REVIEW.md](validation-snapshot/INDEPENDENT-REVIEW.md)。
- 文本来源及摘要：[manifest.json](validation-snapshot/manifest.json)。

快照内路径按原工作区解释。原始 `out/phase28`、私有设备日志、HAP、SDK、二进制与媒体不纳入提交；seal.json 是原封存记录的逐字节副本，不能单凭本快照复现所有本地证据。原封存不修改。

阅读顺序以最终复审及 REPORT 为准。research/quickstart 保留实施前计划语境；tasks 中部分中间运行编号、摘要为历史值，不作为最终产物身份。REVIEW-RESPONSE 各轮记录也不能替代最后 U1 的产物身份。最终源码、构建与 CI 身份见 REPORT 及 seal。

本次提交前检查：Spec Kit prerequisite 通过；已提交 source-index 的 43 项文件摘要匹配；9 个 mpv 源文件及生命周期脚本/harness 与实验工作副本一致；ohdec.c 匹配已提交 FFmpeg 索引；原 verify_handoff.py 校验 53 项 seal、55 项 materials 通过。没有功能改动，因此未重新构建或操作设备。

主仓保持 `yaoshining-hdr-playback` / `1bb2a7c33ed88eafbeb3f42bcc4bf4299797497b` 及历史脏改动。其 index 摘要与旧记录不同，HEAD/分支/已跟踪改动列表匹配；未尝试改写索引来恢复历史摘要。Player/TV HEAD、分支、索引与已跟踪状态及 12 项保护产物匹配，Phase27 snapshot02 封存匹配。

目标设备 GPU/Release 故障注入、同一 consumer 交接与强并发、Start/Configure/fallback/seek/reinit 设备覆盖、物理 HDR 和主观声画继续待验收。隔离诊断审查通过不构成产品发布或候选替换批准。
