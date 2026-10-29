# 内部诊断证据模型

- SourceCandidate：id、官方 URL、完整 revision（适用时）、归档 SHA、顺序化原补丁 URL/SHA、骨架来源、版本；记录字段适用性原因，缺少必需来源时不能进入 verified。
- BuildObservation：candidateId、实际命令/cwd、环境白名单、工具/资源/M4 SHA、输入文件与编译头文件清单、flags、退出码、日志路径；记录生成前后摘要，禁止将事后记录伪称预锁。
- GeneratedComparison：原 stdout 与 Waf 落盘文件分别 SHA、历史参照 SHA、特征矩阵、完整匹配布尔值；特征相等不能自动提升完整匹配。
- ObjectComparison：生成输入引用、目标对象 SHA、历史参照 SHA、节/符号/重定位证据；仅来源生成对象可进入 ArchiveControl。
- ArchiveControl：成员名及 occurrence、顺序、每项来源、归档 SHA、链接命令/map、stdin GOT 与最终库 SHA。
- BoundarySnapshot：封存索引 SHA/项数、业务 HEAD/index、候选/默认 inventory、TV HEAD/HAR/mpv/六库；任一漂移停止依赖该基线的声明。

来源状态：observed → source-pinned → generated-match → object-match → relink-observed；每阶段可进入 excluded 或 unresolved。任何状态不自动代表历史机器实际安装身份、正式产物或设备验收。
