# 实施计划

输入：[spec.md](spec.md)。日期：2026-10-17。

## 技术路线

保留原 build.sh 普通多 ABI 流程；增加 tools/ffmpeg8/producer-sdk.py 作为 TV 基线入口，提供 import-baseline、build、verify。Python 标准库处理 manifest、摘要和安全路径；迁移 build-ohcodec.sh 使用锁定 git archive、校验补丁和静态 sysroot，然后 configure/make/install。重建前捕获工具二进制、完整 NDK sysroot 与缓存 include/pkgconfig 摘要。基线 runtime 与源码重建 SDK 分离，头文件如来自本次构建须单独标注。

## Constitution Check

本仓核查结果：无 .specify、constitution、specs 或 speckit 命令模板。参考相邻 Player 的 Spec Kit 文档结构，但不导入其仓库专属宪章；本次以用户明确规则作为门禁，不宣称运行过不存在的 slash command。遵循 spec → plan/research/data-model/contracts → tasks → 失败测试 → 实现 → 回归。既有改动保留、三仓边界、真实来源/设备状态均为不可绕过门禁。

## 文件布局与验证

- tools/ffmpeg8/baseline-lock.json：可信固定摘要。
- tools/ffmpeg8/patches/ohcodec/：固定上游补丁。
- tools/ffmpeg8/producer-sdk.py、build-ohcodec.sh：导入、构建、核验入口。
- tools/ffmpeg8/tests/test_producer_sdk.py：篡改、缺失、路径逃逸、差异与覆盖拒绝。
- out/vidall-tv-baseline-sdk：导入包；out/vidall-tv-source-build：独立源码构建。
- docs/vidall-tv-baseline-handoff.json：跨会话入口。

先运行离线回归与现有补丁测试，再真实编译 ARM64，进行 ELF/OHCodec/SMB/TLS 静态检查和六库比较。运行成功不等于真机通过。CI 先加入离线合同测试；本机缓存不能虚构为 CI 可用的完整依赖输入。

## 第二阶段计划

先在独立 out 目录做历史 prefix 实验；具体反汇编与字符串证明父仓 Git 版本污染后，先增加失败回归，使用 FFmpeg 自身支持的 revision 输入固定 8.0，并将 configure prefix 与 DESTDIR 分离。用两次独立 clean 构建验证稳定策略，另以历史 prefix 做历史六库全字节验证。所有试验保留独立目录。

官方 Spec Kit 当前稳定版核验为 v1.2.1，先下载/校验官方源码，在本仓 out 隔离 CLI，再 init 本仓（原本没有 .specify）。依赖采用新的 release SHA 锁；历史缓存 git HEAD、dirty patch 与非 git 文件库存只作为现存证据，不推断与历史产物一一对应。CI 使用固定输入包和失败关闭的正式交付门禁。

## 官方初始化后的宪章复核

当前已通过官方 v1.2.1 CLI 初始化；前文无 .specify 是第一阶段事实。feature.json 选择现有 feature，Git 分支保持。setup-plan 跳过已有 plan，分析/实现 prerequisite 均已实际通过。宪章 I–V 与 FR-001–FR-010 一致。没有历史审批被追认；官方 Full SDD Cycle 的人工 review gate 尚未执行，不声称其已获批准。

## 第三阶段实施计划

先保留原 recipe 两次真正 fresh 构建作为比较实验。重复性工具由实际文件生成结果，不接受输入 allMatch。宿主锁在构建前冻结所有执行工具与 NDK/recipe 并在前后重验。修复路径、archive 顺序、生成源等实际差异后另建全新路径复验。Linux 使用官方 Debian 固定 amd64 digest 和签名 snapshot 获取工具，在构建任何目标库前保存 package 版本、deb SHA、命令版本和文件 SHA。宿主获取验证与字节重复性分别验证，历史源码身份仍保留 false。专用远端分支用隔离 Git index 从明确基础提交产生，原分支/脏文件不切换。

## 第四阶段实施计划

先固定fresh TV完整组合与已有SDK manifest。使用已保存构建对象及中间的历史静态输入稳定构建作为控制组，比较历史→稳定配置→新静态输入→Linux工具链的分层差异；新增审计工具先做失败回归，任何构建只写独立out/phase4。缓存只读，不以新实验追认历史。收集配置/对象/归档链，来源声明按证据强度评级。官方SDK获取线索由协调会话并行调查，本会话聚焦本地元数据与历史对象。不改变冻结包、baseline/source锁、Player或TV。

## 第五阶段计划

先重核TV与原缓存GMP配置；真实执行shell构建函数，利用本机静态依赖链和配置探针做RED，修复HOGWEED_LIBS及GMP配置。增加构建后核验：GMP宏、GnuTLS宏、ELF对象内ecc_curves固定AArch64布局中的ID和supported位，拒绝仅字符串存在。记录能力报告与实际归档/config摘要，纳入build record/manifest。复制冻结recipe到out/phase5并预锁当前工具链，两组全fresh构建，随后分别构建FFmpeg并比对。必要代码以隔离index提交专用分支，不切当前分支；云端CI重复同样构建与能力门禁，下载artifact重新核验。

## 第六阶段计划

先fresh核对TV并建立逐项差异矩阵，记录实际探测命令/源码分支/对象和路径证据。先将最小对齐方案写入commentary与handoff，再分别对GnuTLS硬件加速/iconv/包装及Samba平台/生成代码/路径建立RED行为测试；不机械恢复错误宿主配置。对运行路径冲突明确保留分层结论。修复后冻结新recipe和工具，两个新目录全量构建、实际对象门禁、FFmpeg重复验证；隔离index提交专用分支并下载真实CI证据。所有输出out/phase6，旧证据不写。

## 第七阶段方案调查

先验证完整TV组合及phase6所有索引、SDK/包指针；记录业务脏文件摘要。独立解析全部dynconfig变量及直接/访问器引用，追踪Waf Python环境与目标安装路径的关系。预锁真实Bison二进制及骨架文件，分别生成有/无#line的2.3和3.8.2输出，不改旧构建树。以同一组FFmpeg对象做控制重链接，区分版本配置对象、静态依赖与实际ELF差异；所有输出在out/phase7，方案与待确认修改写入analysis-phase7.md。常规目标路径最小方案优先使用上游configure目录选项；Bison默认版本切换与新增来源留待证据和方案确认。

## 第八阶段实施计划与真实顺序

重新阅读约束、完成冻结预检及111项旧回归；新增真实路径/转发器漂移RED先行。首轮最小代码已编辑后才追加本节规格映射，该流程偏差如实保留，不追认规格先行。后续补齐native env-i、非转发工具、资源缺失等失败边界，在测试通过后冻结配方。实际目标路径由上游configure选项产生；Waf禁用状态及ELF指针门禁联合约束。macOS解析全部实际PATH命中的Apple转发入口，保留非Xcode工具；选择器传播到真实构建子进程，M4显式选取已锁工具，生成后Bison资源集合也锁定。Linux保持原默认工具与来源。

最终本机API24两clean、CI OpenHarmony5.0两clean分别报告。下载后重算artifact摘要、SDK清单、静态/FFmpeg交付、Python能力与工具锁证据。旧阶段只作为对照，不当作新阶段验证。
