# Phase26 实施计划

Python3 标准库、C++17/pthread/ASan/UBSan、ArkTS API24 与现有 FFmpeg/mpv 七库。主 checkout 保持分支与已有脏改动；从 Phase24 已批准 6fe31c944edd82b5faafb093bae9336cc40a2e11 的独立 clone 创建 codex/phase26-validation，不触碰旧 clone。

先固定来源和 Spec Kit 文档；CI：允许列表复制 Phase25 实际函数/测试，新增 runner 与 getter 合同测试先 RED，最小实现 GREEN；工作流 Ubuntu22.04。收集源摘要/命令/版本/真实退出码，不下载 SDK，不整目录公开。精确提交/大小/排除清单准备完才申请 push。

HDR：先真实旧日志门禁 RED，新增实际 AVFrame 提取与 consumer ownership 的原生合同测试 RED，再编写桥。桥在 Phase26 独立 App 编译，七库完全不变；direct decoder 与 mpv 串行、原生 worker 独占 consumer。仅 AVFrame 和 buffer descriptor/color，无 GetMetadataValue。devecocli build/run，在设备应用目录 Phase26 取证。

再跑原 PQ1000/PQ2000/HLG/SDR 的公开属性短矩阵及同实例切换（两种后端），先确认安全接口。对需新库的 renderer 内部读回/修复仅报告方案，等具体批准。物理确认缺自动证据时不提前呼叫用户。

设计前后宪章通过：三仓只读边界，真实 SHA，SpecKit/TDD，未追认 CI/设备/发布。官方 setup-plan 已执行；feature env NO_PERSIST 保持既有指针；extensions.yml 不存在。研究三项见 research.md。
