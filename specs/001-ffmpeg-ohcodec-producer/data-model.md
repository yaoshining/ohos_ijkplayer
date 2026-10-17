# 数据模型

SDK manifest schemaVersion=1。artifactKind 仅 imported-baseline 或 source-build。libraries 为六个 SONAME 的相对路径、尺寸、SHA256。其他 inventory 使用相同摘要记录。producer 的 workingTreePatchSha256 对应仅 producer 范围的 git diff 加未跟踪文件补丁（不读取 keys），保存证据文件。sources 使用完整 commit 及 git archive SHA256。tools 记录本次工具的摘要与 NDK sysroot inventory；历史原构建工具无证据则标记 unknown。staticDependencies 明确 digest-verified-cache、rebuiltFromSource=false、fullyVerified=false。rebuildComparison 逐项 expected/actual/matches；与导入的历史声明完全分开。

消费者必须先固定 manifest 文件 SHA256，再核验包内所有摘要，不能仅信任 manifest 自报信息。headers 的 origin 需要明确，import runtime 不自动拥有可用开发头文件。SBOM 是有缺口的库存清单，不等于完整供应链认证。

## 第二阶段扩展

新静态依赖可标记 rebuiltFromSource=true，但 fullyVerified=false。sourceManifestPath/Sha256 将实际八库来源清单绑定到 SDK；新输入清单须包含准确八库（禁止重复）、headers、pkgconfig 并在消费前验证摘要。旧历史清单保留，不冒充新 schema 证明。derived imported SDK 通过 derivation 保存旧包 manifest 摘要，runtimeRebuilt=false。handoff 分开 originalBaselineCommit 和 currentObservedTvCommit，并记录媒体字节是否一致。
