> 后续实施已按 20:15 的直接人类授权完成，最终来源/验证结论见 [Phase12报告](producer-phase12-report.md)。以下是先前方案复核快照；运行目录 API 仍未实施。

# Bison/Flex 与运行目录：最小方案复核

2026-10-18。按用户“先确认最小改动及验证方式”整理。本轮只有证据复核、只读来源调查和规划文档；不实施运行目录 API，不构建或替换候选，不改默认生成器。Player/TV 只读，真机待验收。

## 当前结论

| 项目 | 已证事实 | 最小后续改动 | 验证方式 |
|---|---|---|---|
| HX509 Bison/Flex | 固定 GNU Bison 2.3 + Apple data、Apple flex-35 已能源码复现；独立 profile 已有双平台证据 | 复用现有 profile，无需重做或全局切换 | 引用原始 C/H、对象和现有 CI 实物证据；相关配方变化时才重跑 |
| 剩余 Flex | 另一对象 lex.lex.c.124.o 的历史来源未明；官方 2.6.4 与当前 Xcode 均不匹配 | 新增独立来源记录/特征校验及测试；来源明确后才接隔离生成编译 | 原始来源 SHA → stdout/Waf C → 完整目标对象 → 成员顺序/重链接；大小或版本相同不算通过 |
| 运行目录 | 首次 smbc_new_context 内即初始化全局配置，并读取 HOME；最后上下文释放会清全局状态 | 保留现有显式进程级配置接口方案，先固化路径映射/锁序/失败传播合同 | 首次调用时序、HOME 优先级、生命周期、并发、错误传播、实际文件访问与 ABI |
| Python | 当前已禁用模块并指定目标路径；TV 仍有历史宿主路径指针 | 保留修复；不自动创建 Python 目录，不恢复宿主路径 | 检查真实配置参数、对象数据与最终 ELF 两个有效指针，不能只搜索目标字符串 |

## 运行目录方案需要确认的行为

沿用 phase9 提案，不新增第二套 API 设计：一个版本化配置入口（暂名 ohcodec_smb_runtime_configure_v1），在首次 SMB 上下文创建前传入显式配置文件、持久状态根、缓存根和只读资源根。目录由调用方创建；producer 负责校验和使用，首版不递归 mkdir，不改 HOME。API 尚未实施。

显式模式跳过 HOME 配置及 append，保持指定目录在 loadparm 初始化后的优先级。配置先完整校验/复制，再一次发布；相同配置幂等，不同配置或旧方式已启动返回冲突。配置跨最后上下文释放继续有效；不可回滚的全局初始化失败进入失败状态，不能静默退回 HOME。未调用接口继续兼容旧模式。

实施前必须逐项确认 28 个 dynconfig 项目的客户端访问和资源交付；state/private/lock/run/log、cache、codepages/modules/lmhosts 只是已提出的映射方向，不冒充全部已验证合同。需要真实进程锁，不能仅依赖可能退化为空操作的 SMB_THREAD 宏。接口拟只增加一个导出和开发头文件，Samba 内部 hook、FFmpeg 包装/导出表及构建登记是必要实现触点。

对应测试先 RED→GREEN：路径缺失/相对/权限错误、空配置及解析失败、同配置重复/冲突/调用过晚、并发首次创建、最后释放后重建、ENOMEM、HOME 冲突与 append、未配置兼容行为。检查实际访问路径、目标链接及导出变化；宿主检查不替代设备目录权限和 SMB 播放验收。运行接口实现会改变行为和库字节，不计历史字节复现。

## 来源诊断的停止条件

未找到原始来源补丁时只交付排除矩阵，不手工修生成 C、不恢复历史对象。即使 lexer 源码对齐成功，保留 Python 目标修复也无法使 avformat 全文 SHA 等于当前含宿主路径的 TV。当前 API 工作保持方案阶段；来源诊断按独立 Phase12 计划继续拆分，不改默认或消费端。

## 本轮验证与证据

`out/phase12/solution-review-boundary.json`：重新核验 Phase11 24,224 项 SHA/大小/已记录软链目标、候选及默认 SDK inventory、TV HEAD/HAR/mpv/六库、业务 HEAD/index 和 feature 指针，全部通过。Phase11 索引 SHA 为 8a5b4b2f814c92b40eff1e0ca4886d758a96c1364673f44ae33d5de44ed73e55。

依据：`docs/producer-phase9-source-report.md`、`docs/producer-phase9-proposal.md`、`docs/producer-phase11-report.md`、`out/phase11/source-research/result-summary.json`。本轮重新读取实际 Samba libsmb_context.c 的初始化/清理逻辑及 dynconfig.c 项目。更新后的来源诊断设计在 `specs/001-ffmpeg-ohcodec-producer/phase12-lexer-source/plan.md`；新功能 TDD、构建、CI 和运行目录 API 均未在本轮执行。

新增只读来源矩阵另见 `out/phase12/upstream-research/report.md`：upstream 2.6.0–2.6.4 五个正式标签所核验骨架的特征均不匹配；已固定的当前 Homebrew 配方及 Debian 2.6.4-8.2 补丁也未解释历史类型组合；未排除全部历史 Homebrew/其他下游。研究清单 66 项独立摘要复核通过，精确来源仍未找到，未做新的生成/编译。

来源排除限定于实际核验的源文件/原补丁。标签骨架分析不等于五套发行工具都已构建验证；发布归档中的预生成 skel.c/scan.c 与 flex.skl 可能不同，实际构建必须绑定真正编译的输入。Phase11 仅官方 2.6.4 已有实际工具/生成/对象不匹配证据。
