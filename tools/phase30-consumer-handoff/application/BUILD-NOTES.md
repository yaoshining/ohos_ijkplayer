# Phase30 应用文本输入包

此说明是本轮 CI 打包说明，不是冻结 HAP 的原始构建输入；原历史说明仅保留在本地 application-final-source-a/03 快照。

当前目录包含实际 A/B 应用的自有文本和所用第三方头。当前 expected.h 对应 B，A 对应文件在 ../application-variants/trace/expected.h。不包含 HAP、动态库、SDK、签名配置、凭据、私有媒体、图片或字体文件；非文本资源 SHA 位于 ../application-variants/nontext-resources.json。

本地实际目标构建使用锁定 API24 SDK 与依赖，临时只读签名链接已移除；具体命令、编译依赖、冻结源码索引和 HAP 清单在本地 Phase30 证据中。CI 仅宿主重放，不执行 hvigor 或设备命令。缺少私有签名与目标输入时不能据此目录单独生成可安装 HAP。

formalArtifactAllowed=false；候选替换、正式应用接入、产品发布均未授权。
