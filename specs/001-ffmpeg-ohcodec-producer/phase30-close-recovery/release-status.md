# PR 前交付门状态

2026-11-10。用户要求补齐流程、通过 PR 合并 master 后再交付；此前本地 SDK 是已验收候选，此文件不把候选当作已合并交付。

- 源码基线：master `33165069ce02718b63689e7c1f4a4256dcba31ae`。
- 原修复提交：`f23b708c4ddea6f03ddea6f7859c1cc07641aeb9`，本次只移植该提交，不带入历史分支实验链。
- 六库 SDK 归档 SHA256：`eb069effc2ce51233186e5e033a2f8bf33f5317a27e4626ba50184807422aea0`。
- 正常构建来源：本地，非 GitHub Actions 目标构建。三根六库一致；正常库真机回归已完成。
- PR 前文档与本地检查：见 `analysis.md`；原版/候选各 8 项实际函数回归通过。
- 提交时 PR、CI 和合并尚未发生，T013/T014 保持未完成。实际事件由本分支 PR 页面、Actions 记录和合并后的 `out/phase30-close-recovery/delivery/merged-source-binding.json` 记录，避免在被合并的提交内虚构其未来 merge SHA。

最终绑定需包含 PR URL、PR head、merge SHA、master 读取结果、各项 CI 与未解决评审状态、产品文件逐项摘要，以及 SDK archive/manifest 摘要和全部清单文件校验结果。任何产品文件变化均需重新评估旧 SDK/设备证据；不能仅用提交标题证明一致。

本次交付范围保持 FFmpeg SDK。Player/TV 未接入，未发布新的消费者 HAR。

## 实际 PR

[PR #11](https://github.com/yaoshining/ohos_ijkplayer/pull/11) 已创建，目标 master。首轮新增恢复回归、PR1、PR3 完整宿主矩阵及汇总通过；源码闭包构建仍在运行。自动评审提出的未提交文件链接已修正；更新提交必须重新等待相关检查，旧提交绿灯不代替新提交。实际最终 head/merge/检查状态以 PR 与交付绑定为准。
