# 验证合同

实际场景矩阵：NAS短冒烟 → NAS连续60min；独立NAS operations（双向seek、暂停恢复）；本地3片切换；前后台恢复；应用关闭/新进程重开。可先执行无凭据的本地场景，NAS凭据缺失不得伪用本地片代替指定NAS。

所有成功必须有当前runID/PID的实际文件加载、有效PTS与恢复进度。seek目标误差2s，暂停稳定3s漂移0.25s，恢复推进3s，片源代次3。长播采样gap15s、实际连续3600s，心跳gap15s、query/sample无悬挂配对；单调时间不得倒退。外部查询timeout/Offline/语义错误/缺记录全拒绝。

敏感输出：NAS只用别名，mpv原始日志禁用，私有配置程序直接读写；CI只明确允许的文本源码/测试和脱敏摘要，不收媒体/库/HAP/SDK/签名/凭据/原始设备日志。

操作采样100ms；seek命令后的SEEK/RESTART/目标样本15s期限，前台恢复15s期限后推进>=3s；命令阻塞由独立app terminal/watchdog与外部短场景150s collector总期限（操作场景app内部120s；长播外部3900s总期限，均含启动收尾）保证FAIL而非无限等待。前后台PASS要求同PID/session/player实例且无SurfaceDestroy/新FILE_LOADED，重建成功仅另列、不替代恢复。正常退出使用terminateSelf（SDK明确killAllProcesses用于异常退出）；30s内查询，正常Ability关闭重开允许缓存同PID但必须新Ability/session身份；新PID验证另列正常清理后外部终止冷重开，不称自然退出。

暂停稳定窗口要求连续有效pause=true样本且间隔<=0.5s；false、查询失效、间隔超限或单调时间倒退直接失败，不跨缺口累计暂停时长。
