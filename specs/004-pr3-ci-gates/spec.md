# PR3 宿主 CI 门禁

补齐 PR #9 在真实合并版本的宿主契约，旧阶段记录及工作流保持原样。正式产物允许仍为 false。

- FR01：pull_request、master push、merge_group 和手动运行执行 11 项矩阵，任一失败、取消、缺输入不得绿色聚合。
- FR02：绑定实际 checkout/tree/parents；PR 必须为 event base/head 的合并版本，不能把原分支或旧 CI 作为此次证据。
- FR03：真实运行阶段契约及 RED/GREEN、失败注入，完整父链、normal 公共 ABI、consumer 互操作、正常操作离线门禁均覆盖。
- FR04：只上传文本证据，依赖工具、上游下载、固定哈希、制品索引错误均失败。
- FR05：不连接设备、不重跑长播、不改 TV、不替换候选。不声称新目标库/HAR 构建或真机验收完成；旧失败不改写。

Phase21 仅资源工厂宿主合同，不执行依赖历史 Actions artifact 的完整 native/target 构建。目标构建由 PR1/PR2/Player 独立门禁负责，不能把本门禁成功解释为全部 native 库重建。
