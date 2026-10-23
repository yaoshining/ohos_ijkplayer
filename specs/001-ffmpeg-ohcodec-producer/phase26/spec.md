# Phase26：Phase25 Linux CI 与 HDR 分层验证

授权：2026-10-21 人类消息 01a15a9d-1e0a-7e03-a0f5-aaf1b5abcaa2，已直接核对。Phase25 已封存，不修改旧快照。Player/TV 全目录只读，候选不替换。

## US1（P1）可复核 CI
维护者需要把最终 Phase25 诊断的 16 项 Python 测试与实际原生函数放入独立 Linux CI。独立验收：允许列表来源一致、实际函数 ASan/UBSan、失败不伪装成功、精确提交与工作流绑定；新 push 另需精确授权。
## US2（P1）HDR 解码证据
使用原七库和原创 PQ1000/PQ2000/HLG/SDR，获得实际 AVFrame MDM/CLL 及独立 consumer 的真实分配描述。独立验收：夹具/库/HAP/源码/maps 绑定，软硬串行、帧和 buffer 关联；缺失 metadata 明确失败，不以 EOF 通过。
## US3（P2）输出与物理边界
核对同实例同 PQ transfer 的 1000→2000→HLG→SDR；未获真实窗口所有权不并发 Get，不以 Display 能力代替面板状态。必要新库仪器化先报范围；现场确认仅具体可观察场景就绪后请求。

## 功能要求
- FR01：冻结 Phase25 和旧证据，全部新增输出在 Phase26；禁改候选、Player/TV、系统设置。
- FR02：CI 使用实际冻结来源，16 项 Python、时间线原生函数 ASan/UBSan；新增 getter stub-link 覆盖单列，不称设备执行。
- FR03：runner 校验来源；失败保留退出码；收集严格允许列表，排除凭据/HAP/库/SDK/设备隐私；新精确提交先预览后授权 push。
- FR04：解码诊断保持七库、各层证据独立，PQ 缺 MDM/CLL 不通过；HLG/SDR 不强求 HDR10 静态字段。
- FR05：consumer 独立且单线程 acquire/read/release；AVFrame token 不强转为 NativeBuffer；fence 与引用严格归还。GetMetadataValue 所有权未明，不使用。
- FR06：继承应用保屏 request/success/readback/release、独立时间线；只使用应用保屏，不改系统设置，不模拟保活。唯一设备操作者本会话。
- FR07：明确同 transfer 不同亮度更新；真实 mpv 窗口和物理 HDR 未证保持 pending。若改 libavcodec/libmpv，先单独说明范围与风险。
- FR08：收尾清理派生配置/运行计划并停止诊断，保留原始失败，旧封存与产品 SHA 重核；formalArtifactAllowed=false。

## 成功标准
SC01：本地完整 CI 入口通过；获新 push 批准后有真实 Linux run 与制品校验，未批准不得写 CI 成功。
SC02：原七库下取得本轮实际解码证据并逐项判定，缺失允许作为已确认失败，不以未修复阻塞事实报告。
SC03：旧封存、产品、系统边界不变；设备/输出/物理验收逐层说明。
