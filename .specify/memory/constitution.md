# ohos_ijkplayer 项目宪章

## 核心原则

### I. 三仓唯一职责与冻结边界

ohos_ijkplayer 必须唯一生产 FFmpeg/OHCodec 与 SMB/TLS 依赖。VidAll_Player 只消费固定 producer manifest，负责 mpv/HAR/组合清单；VidAll_TV 只集成统一组合与验收。本次 Player、TV 全目录只读，包含文档、锁、候选与输出；禁止在两仓写入。不得读取 keys；保留既有无关脏改动，不切分支、不重置、不清理工作树。

### II. 当前 TV 字节基线优先

开工必须重新核对 TV HEAD、HAR、HAR 内 libmpv 和六库 SHA256。tag、版本、缓存、源码锁都不能代替实际制品摘要绑定。任何差异必须先报告；imported-baseline 不得被重建产物覆盖。历史字节复现与新构建重复性必须分别记录。

### III. TDD 与真实执行顺序

功能与缺陷必须先写回归并观察失败，再实现并验证正常、边界、失败路径。运行真实构建和针对风险的检查；保存 RED/GREEN/构建日志。不得追认虚假的先后顺序、审核、审批或成功。用户已授权的常规实现、修复、初始化无需重复请求确认。

### IV. 来源与产物闭包

源码归档、完整提交、补丁、工具链、静态输入、运行库、头文件、pkgconfig、许可证和 SBOM 必须绑定摘要。新选 release 源码不得冒充历史 git/cache 来源。不能证明完整闭包时必须 fullyVerified=false；正式 CI 产物门禁失败，禁止以普通 FFmpeg 绿灯代替 OHCodec。

### V. 设备与发布边界

source-build、imported-baseline、可重复构建和设备验收分别表示。设备一律 pending，不继承历史交付验收；编译/链接/ELF/HTTP 成功不等于播放成功。未经新授权不发布、不推送、不部署设备。

## 开发流程

真实 Spec Kit 项目状态由 .specify/feature.json 选择 feature，与 Git 工作分支解耦。保留 spec → plan/research/data-model/contracts → tasks → analyze → implement/check 的证据。新需求补入已有 feature，记录原文档先于官方初始化的事实。官方脚本的 prerequisite 检查必须实际执行；语义分析须由开发者阅读工件并输出，不能拿脚本退出 0 代替。

## 治理

本宪章依据本次用户明确授权初始化。中文是默认文档语言。规则改变需记录来源和影响，不能为通过门禁稀释验收。Spec Kit CLI/模板固定官方版本，项目隔离安装，不更新全局其他项目。旧证据和清单保持，新增结果使用独立路径。

**Version**: 1.0.0 | **Ratified**: 2026-10-17 | **Last Amended**: 2026-10-17
