# Phase24：指定 NAS 长播与 HDR / 10bit 分层验证

创建：2026-10-20。状态：设计完成，执行待补。现有checkout不切分支；隔离提交使用codex/phase24-runtime-evidence。
授权：主会话01a1460e-abce-7e50-971e-ba699c8b9116，人类消息01a15900-27d7-7f30-a08c-ed6924462a82：继续协调补齐真实SMB长播和HDR/10bit，按SpecKit/TDD，Player/TV只读、不替换候选，差异先报告。具体私人影片仅保存本地私有配置，公共证据称nas-media-01。

## 用户场景与测试

### US1 指定NAS连续长播（P1）
独立测试：同一播放器实例、1x速度、至少3600秒连续单调钟窗口及媒体进度。记录输入时长/编码、缓存停顿、资源和音频管线。
1. 时长足够时无seek/重启/loop/暂停地完成窗口；不得用累计短播代替。
2. 提前EOF、失去硬解、进度停滞、指标不可用、错误或中断保留原始状态，不判通过。
3. seek与重连恢复独立短测或在窗口之后，不计入连续时间。影片不足一小时先报告，不静默循环。

### US2 HDR / 10bit分层证据（P1）
独立测试：10bit SDR、HDR10/PQ、HLG可信像素样本，GL/Vulkan × OHCodec/软件对照。输入位深、真实decoder、GPU输出位深/色彩、系统设置结果、显示声明、人工观感独立记录。
1. 输入码值/metadata验证通过才进入矩阵，出帧不等于HDR输出正确。
2. 默认GL实际8bit如实报告；显式10bit配置单列。软件成功不覆盖硬解失败。
3. 同实例HDR→SDR→HDR与同transfer不同metadata切换观察恢复；无法可靠观察保持未知。

### US3 证据与冻结边界（P1）
独立测试：旧封存/候选/Player/TV前后摘要和状态不变，新HAP/源码/七库/maps一致，私人名称和凭据不进入日志/hilog/CI。

## 边界情形
认证失败、中文及percent-encoded路径、提前EOF、设备离线、无音轨、属性缺失、HDR能力缺失、颜色API失败、旧metadata缓存、取消和Surface销毁均须保留失败/未知。

## 功能要求
- FR-001：只写Phase24目录，Phase23及更早封存、候选/default、Player/TV全目录不变，保留无关改动。
- FR-002：只读打开指定NAS文件，不列目录/扫描账户。用户提供配置后读取；私人影片不入CI。
- FR-003：长播以单调钟和连续媒体进度共同证明至少3600秒、1x；无loop/seek/实例更换/提前EOF/软解fallback。PTS采样次数不称presented frames。
- FR-004：每5秒属性/错误码，每30秒fd/线程/RSS；记录可得的demux/cache/bitrate、drop、avsync、AO、hwdec。不可用保持null+error，吞吐估算说明来源。
- FR-005：所有播放器日志写入前处理；NAS仅白名单结构化字段，禁止原始debug/error文本和私人路径。认证不进入URL/命令行/CI/普通源码。
- FR-006：三类HDR样本绑定SHA、生成来源、像素独立校验和ffprobe；PQ含MDM/CLL，HLG不要求HDR10静态metadata。
- FR-007：输出位深读取EGL选中配置/VkFormat；API失败保留。不并发调用非线程安全NativeWindow getter，不为验收改窗口状态。内部实际P010分配未观测则未测。
- FR-008：真实RED→最小实现→GREEN，保留失败；初始沿用Phase23实验七库。必要库修复先报告，独立来源TDD/双clean/新maps。
- FR-009：主代理唯一设备操作者，仅指定电视独立诊断bundle。现场听音/物理声画/HDR观感待人工，Dolby Vision未测。
- FR-010：SpecKit官方模板/初始化/prerequisite与人工语义分析保留，隔离CI仅源码/规范/脱敏证据。正常继续授权不另设审批门槛。

## 关键实体
Session：实例、时钟、maps、样本ID。Observation：值/错误/时刻。Media：类型/位深/来源SHA。Verdict：每层独立状态。PrivateConfig：外部凭据不进入公共证据。

## 成功标准
- SC-001：指定影片完整连续3600秒实测，全部中断和未知可见。
- SC-002：三类输入×两GPU×两decoder逐项结果/阻断，颜色切换单列，不笼统宣称支持HDR。
- SC-003：泄漏/中文路径/短时间/EOF/fallback等负例及正常场景真实RED/GREEN通过。
- SC-004：旧边界复核、新执行输入绑定；真机/人工/正式交付分别给状态。

## 假设
NAS指定路径是唯一允许访问的媒体，认证配置待保存。设备离线期间独立准备主机测试。自建静态HDR短样本不代替真实影片或物理校准。不能确认的输出状态保持未知。
