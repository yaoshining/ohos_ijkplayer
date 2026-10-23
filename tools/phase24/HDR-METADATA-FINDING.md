# OHCodec HDR10 静态元数据缺口：实测与最小修复方案

2026-10-20。状态：**已有目标实测RED，尚未改库/修复**。本轮继续验证Phase23原七库；不覆盖候选、Player、TV，也不把软件路径作为硬解替代。

## 实测范围

同一原创PQ文件（SHA256 `2e795cb3a1d1694ba7d0c0893d8a381bf9151647ec6c7a5b4296750684fd7147`）、同一设备/API24、同一HAP与七库、仅切换hwdec：

- `experiments/hdr-01/logs/gl-pq-2.log` / `vk-pq-3.log`：`hwdec-current=ohcodec`，`video-dec-params`有P010/PQ但无min/max-luma与CLL；`video-target-params`max-luma/max-cll为10000。
- `gl-pq-sw-8.log` / `vk-pq-sw-9.log`：`hwdec-current=no`，解码参数max-luma=1000、max-cll=1000，目标仍1000。
- 输入ffprobe首帧明确包含MDM 1000nit和MaxCLL1000。四条路径均出帧到EOF，故EOF不能充当HDR完整性判据。
- 这证明当前OHCodec→mpv可见元数据链存在缺口；尚未直接采集OHCodec内部AVFrame side data和系统composer，不能声称已测得系统实际10000nit输出。

## 源码定位（Phase23只读来源）

根：`out/phase23/ffmpeg-input/source`。

1. `libavcodec/ohdec.c:143-208,969-973`：输入HEVC会拆AnnexB NAL，但仅解析Dolby RPU（UNSPEC62）；没有解析HDR10 mastering display / content light的SEI。`1080,1092`声明hevc_mp4toannexb，最小方案可复用已进入解码器的AnnexB数据，不能另假设原MP4包格式。
2. `ohdec.c:410-516`：stream-changed读取矩阵、primaries、transfer、range、位深等；没有读取或创建MDM/CLL。
3. `ohdec.c:722-769`：硬件输出调用`ff_decode_frame_props`后包装buffer，最终仅`oh_decode_attach_dovi`。没有HDR10 side-data创建。
4. `libavcodec/decode.c:1439-1533`：通用props只复制已有coded/decoded/packet side data及颜色字段，不负责解析HEVC码流中的SEI。因此不能用再调用一次frame_props修复缺失。
5. `libavcodec/hevc/hevcdec.c:3096`与`h2645_sei.c:606-701`：软件解码有SEI→AVMasteringDisplayMetadata/AVContentLightMetadata转换（包括G/B/R顺序和有理数尺度）；同片软件实测也保留1000。
6. `out/phase23/input-package/sources/mpv/video/mp_image.c:1168-1175`读取AVFrame MDM/CLL给libplacebo；本轮不优先改mpv目标峰值，也不硬编码1000。

结论：最可信的断点是OHCodec包装层未把码流HDR10 SEI转为输出帧side data。具体补丁仍要用真实函数回归和诊断日志确认，避免将源码推断写成已修复。

## 可审阅的最小方案（未实施）

- 只在新的Phase24 FFmpeg源副本修改OHCodec侧，复用现有HEVC NAL拆分与FFmpeg H2645 SEI结构/转换，解析MDM与CLL；不改色彩空间选择、GL窗口格式或mpv tone mapping默认。
- 输入端维护有效静态metadata状态，并按本次generation及对应PTS把快照附到异步输出帧；正确处理B帧重排、同transfer 1000→2000变化、flush/seek/重建、缺失与错误SEI。不能拿最近输入包的metadata盲配较早输出帧。
- 输出端在已有props基础上附加MDM/CLL，尊重容器/帧side-data优先级，避免重复/覆盖有效已有值；分配失败按现有release路径清理，不引入新的wrapper/fence泄漏。
- 不把HDR10扩展成Dolby Vision/HDR10+接受结论。原有DOVI队列保持隔离并加无回归检查。

## 修复前必须RED，修复后才GREEN

真实源函数测试：1000nit/CLL1000精确有理数与色坐标；MDM-only、CLL-only、无HDR；畸形/截断/溢出SEI；1000→2000同transfer；PTS重排；flush跨generation不串metadata；内存分配失败与原DOVI清理。

受影响库独立两次clean来源闭包/摘要比较；新HAP、maps、输入哈希全绑定。设备重跑PQ硬/软GL/VK、HLG/SDR负例及同实例切换，期待硬解video-dec-params出现正确1000/CLL1000。随后再分别核验输出配置和系统metadata状态；即便修复解码层也不自动获得物理HDR验收。

本轮交付只提交诊断与此方案，库修复/新库构建未启动，等待主会话确定后续范围。
