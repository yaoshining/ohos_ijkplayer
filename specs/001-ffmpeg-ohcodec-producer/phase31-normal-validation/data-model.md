# 数据模型

RunIdentity: runID、mode、PID、session、HAP/library/source/compile摘要、启动与结束单调时刻。
Action: actionID、kind、target、invoke/return mono、rc、前后property回读、相关SEEK/RESTART/LOADED/END事件序列。
Observation: monotonic、video/time PTS、speed/pause/cachePause及各rc、hwdec/ao/gpu、资源观测。缺失=null，不以零代替。
Lifecycle: 同session的Ability/Stage/Window及keepAwake request/readback；关闭后外部有效查询与新PID。
Verdict: 每项PASS/FAIL/PENDING与原因、覆盖边界、原始证据引用。humanAudioAccepted/physicalHDR=false直至现场确认。
