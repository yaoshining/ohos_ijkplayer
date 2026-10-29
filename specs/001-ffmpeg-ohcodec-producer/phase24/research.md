# Phase24 研究决策
## HDR观测
Decision：用现有EGL/VK配置日志、mpv Node属性和显示声明，不先改七库。
Rationale：输入P010/目标PQ不证明输出10bit；NativeWindow设置失败仅warn，getter非线程安全，实际decoder格式有profile推断路径。
Alternatives：盲目强制RGB10或并发getter会改变行为/引入竞态，拒绝。若现有观测不足，记录未知，必要时另立诊断库来源及双clean。
依据：out/phase24/research/hdr-contract.md的源码/SDK逐项引用。源码风险未当成真机缺陷。

## 媒体
Decision：原创数学PQ逆EOTF/HLG OETF/BT709渐变、灰阶、色块，12秒Main10，绑定码值和SEI。
Rationale：已核查公开素材授权/下载限制；原创避免把SDR改tag冒充HDR。
Alternatives：营销影片/无许可镜像不采用；短图案不能替代指定NAS长播。
依据：out/phase24/research/hdr-media.md。主流程需正式TDD生成，不直接把研究临时文件算验收。

## NAS与日志
Decision：只用用户指定文件和明确提供的外部配置。先精确文件预检，电视真实播放；不扫描共享。认证通过AVOptions/现有安全接口，不嵌入URL。中文路径raw/编码等价测试。
Rationale：原25秒探针和8MiB读取不足60分钟；私有路径可能从日志泄露，NAS禁止原始mpv日志，采用白名单值并保留查询错误。
Alternatives：隔离SMB服务可短测，但不能替代真实NAS；累计短播/倍速/静默loop不可接受。

## 未满足的执行前提
电视连接已失败并告知主会话；等待用户恢复。凭据外部模板待用户保存，未读取。无需改变技术设计或冻结边界。
