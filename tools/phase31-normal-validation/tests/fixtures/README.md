# CI 夹具边界

`operations.log` 与 `switch.log` 仅保留验收所需的相对时间、数字返回值、PTS、加载代次和有限枚举。生成时逐行白名单选择，并对观测 JSON 再按键白名单裁剪；没有 PID、原始媒体名、NAS 路径、mpv 原始消息或设备查询输出。这些是最小字段脱敏夹具，不是 CI 执行设备的证据。

`background.json` 与 `close.json` 由 `../make_synthetic_fixtures.py` 从零生成，是明确的合成正常/失败门禁输入，没有复制真实设备时间线。合成会话/PID 与时间均为固定测试值。

本地可用 `PHASE31_RAW_EVIDENCE` 指向本轮私有证据目录，重放相同门禁的原始日志；CI 不设置此环境变量，也不打包该目录。
