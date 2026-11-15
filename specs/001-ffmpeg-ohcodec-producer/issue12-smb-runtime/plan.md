# 实施计划与分析

根因：普通 build.sh 只应用凭证补丁，build-libsmbclient.sh 默认没有 phase20 的运行时补丁；ARM64 phase20/后续交付链已独立使用该实现。

直接复用 phase20/apply.py 与四个 runtime 文件，不复制出另一套实现。x86_64 的软件 SDK 构建显式开启 Samba runtime 开关，再应用 FFmpeg header/wrapper/version-map 补丁。其他生产链默认行为保持。复用旧静态 sysroot 时必须校验真实内部符号，拒绝未打补丁的输入。

先记录旧包 RED 和新增测试，再接入；从校验后的源码缓存在新目录构建全部依赖与 FFmpeg。冻结源提交后构建，补丁证据、实际 recipe/runtime 文件和宿主信息随包交付。强化 audit 与消费者，发布独立新附件，回读核验后回复 #12。

## 语义与一致性分析

runtime 是 C/POSIX，当前未发现 ARM64 专属指令或 ABI 常量；两目标均为 64 位。公开结构逐字复用，所有权与状态机不改变。SMB 前缀虽有 ohcodec，与 av_ohcodec_* 硬解合同独立。最终实际 x86_64 交叉编译与链接验证此推断。

FR-01/02/03 → phase20 runtime/patch + 主机语义/顺序回归；FR-04 → audit、独立消费者、真实产物；FR-05 → package/manifest/source bundle；FR-06 → issue/Todoist 交付。无互相冲突需求。原 feature 历史未完成任务不冒充本轮任务；本补充没有 reviewer checklist。官方 prerequisites 已运行。用户范围仅 SDK，TV/HAR 历史冻结核验不扩展到本轮消费者访问。

## 评审后来源门禁

首轮实际构建与手工保存的 e562501 输入一致、链接通过，但通用打包入口曾依赖当前 HEAD，不能拒绝未来复用旧 sysroot 的误归属。新增失败回归后，在依赖与 SDK 构建前捕获源提交、全部配方/共享 runtime/补丁与关键工具摘要，完成后验证输入未变并封存 lib/include 实物摘要。打包必须核对两个构建记录、当前输入与实物一致，SOURCE.json 和 manifest 从构建记录取提交。缺标记、代码/提交/工具或库漂移均拒绝，需全新构建。初次候选包不发布，保留诊断后重新构建。带点版本名的源码归档须追加扩展名，不替换已有后缀。
