# Phase24 实施计划
日期2026-10-20，输入spec.md。主checkout不切分支，产物仅out/phase24。

## 概要
复制Phase23独立诊断应用，保持七库和签名。先补纯函数验收/日志策略与HDR生成器的真实RED/GREEN，再接入C++低频采样、NAS私有配置、ArkTS调度。NAS长播和HDR分层结果独立。

## 技术上下文
C++17/NAPI、ArkTS、Python3标准库；现有mpv/FFmpeg七库、DevEco工具链、主机FFmpeg8/libx265。目标为已授权MateTV API24（连接待恢复）。测试用Python unittest、host C++策略测试及实际devecocli构建/指定电视运行。采样5秒，资源30秒，长播至少3600秒。原始私人信息不写日志；只读指定文件。设备/凭据未就绪是执行前提，不阻止主机设计实现。

## 宪章检查（研究前与设计后）
通过：新授权支持独立设备诊断；前置边界已实查。Player/TV只读、旧封存不改、无关改动保留。TDD必须保存实际RED；初期仅改探针不改七库。新库若必要则先报告+新来源双clean，不继承旧验收。正式交付状态仍pending。无宪章例外。

## 结构
- specs/001-ffmpeg-ohcodec-producer/phase24：规范、研究、合同、任务。
- out/phase24/app：独立诊断应用副本，原签名引用保持，不读取keys。
- out/phase24/tools、tests：可独立CI的源码/测试。
- out/phase24/private：本机私有媒体映射/连接配置；凭据在用户指定外部临时文件，禁止纳入CI。
- out/phase24/fixtures/hdr：原创短图案及生成、编码和像素验证证据。
- out/phase24/experiments：HAP绑定、设备日志、分项结果。

## 顺序
研究已委派两个只读代理并汇总research.md。完成合同/任务/语义分析后实现。先用短测确认maps/日志/输入，再长播；长播运行中不部署或操作同一设备。人工确认仅在稳定画面可见时请求。

## 最小改动
仅新增诊断策略/采样/调度/主机工具；旧七库保持。优先现有EGL/VK配置日志与mpv属性，显示能力只读；不并发调用NativeWindow getters。独立短矩阵可开启debug，NAS禁用原始mpv文本输出。缺少可靠内部分配/metadata观测明确未测，不冒险写窗口状态。
