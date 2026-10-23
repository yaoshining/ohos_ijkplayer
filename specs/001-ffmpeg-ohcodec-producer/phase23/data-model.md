# 数据模型

Experiment包含id/story/sourceCommit/patchSHA/toolchainSHA/inputLibraries/builtLibraries/device/bundle/mode/time/result；未知明确unknown。
ResourceSample包含cycle/surfaceId/stage(before/playing/destroyed/settled)/time/fdTotal/fdTargets/fdInodes/threads/RSS/collectionErrors，失败读取不记0；热身与稳定期分组。
SmbCase包含endpoint/credentialCase(correct或wrong，不含密码)/clientLayer/errno/AVERROR/NTSTATUS/serverRequest/bytes/SHA256/seekRanges/reconnect/result；TCP成功不等于认证成功。
SourceBinding记录原始完整commit/归档SHA、复制前后SHA、补丁、命令、工具实际SHA、静态输入、输出ELF与目标maps。
状态依次planned/reproduced/diagnosed/patched/host-verified/target-verified；failed和blocked独立保留，各项不得互相继承。
