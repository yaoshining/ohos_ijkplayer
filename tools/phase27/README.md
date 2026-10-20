# Phase27 HDR 修复验证

OHCodec 首帧缺少静态亮度元数据，mpv 的同 PQ 更新还会读取旧 VO 参数并跳过窗口提交。本轮在固定 FFmpeg 和 mpv 源码上修复这两条链路。连续视频的设备失败又定位到 Annex B 过滤器插入旧 extradata 的顺序，以及 helper 绕过 FFmpeg side-data 优先规则；当前回归包含这两个真实失败的修复。

执行 `python3 -B tools/phase27/runner.py --out out/phase27-ci`。要求干净 Git checkout；开发阶段可显式使用 `--allow-dirty`，其状态仍记录到证据中。runner 下载固定提交及 SHA 的 FFmpeg 归档，应用完整补丁，核验 9920 个源文件的集合、大小和摘要，构建真实上游 SEI/parser/转换静态对象，再执行：

- 23 项 mpv 实际函数切片回归，含当前帧、target 限制、SDR、缓存与失败重试。
- HDR helper 与真实 ohdec send/output 连接、重排/事务/未知和重复 PTS/IRAP/flush/OOM。
- 既有字段与 DOVI、队列上限、EOS/BLA、多 slice、generation 隔离。
- 真实 hevc_mp4toannexb：prefix SEI 前后参数集、IRAP 与普通帧、extradata 单独使用和实际 NAL 数量。
- 真实 FFmpeg 默认码流优先与显式 packet/global 优先。
- 来源/路径/额外文件/符号链接/二进制收集拒绝及隐藏工作流索引门禁。

ASan/UBSan 设置为遇错失败。FFmpeg 使用实际完整上游对象；mpv 平台接口与 ohdec 外部平台 API 使用明确桩，不能把它们声称为目标运行或 GPU 验收。动态库、HAP、SDK、签名、凭据及媒体夹具均不包含在此提交或上传中。只上传 `artifact/` 允许的文本证据，包含本轮执行源码、真实工作流、Git HEAD/dirty、前后输入摘要和全部文件索引；测试与收集结果分别标记。

Vulkan 释放诊断代码仅作来源审查，不把日志插点作为释放告警修复。真机、窗口 metadata readback、物理 HDR、产品基线与正式发布验收分别记录；本 CI 不替代它们。未知 PTS 或多 AU 布局歧义时，本代次静态 HDR 关联禁用到 flush，解码继续；不宣称这种输入完整支持 HDR。队列上限仍以明确错误返回，不静默错配。
