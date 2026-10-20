# 诊断合同
长播成功要求：单调钟elapsed>=3600、sample间隔不超过15秒、media进度与1x墙钟匹配（允许启动前缓冲，窗口从首个推进样本开始）、无seek/restart/loop/暂停/EOF/错误/软解fallback，实际硬解每样本可观测；AO/音频管线仅有音轨时单独验收，无音轨记not-applicable。5秒连续无进度记录stall，超过15秒判连续窗口失败；不能用缺失值0掩盖。长播不设短25秒deadline；可在3605秒完成预留采样。资源/吞吐/可选缓存属性有缺项则分别unknown，不替代核心判定。长播窗口之后再seek/重连。
NAS日志仅允许结构化数值、已知枚举和sampleId；不输出mpv原始prefix/text。所有字符串经过private-token/URL脱敏兜底，错误保留数值。中文路径UTF8百分号编码一层，防双重编码、错误解码凭据；SMB URL无userinfo，认证由AVOptions。异常不能回显私有输入。
HDR短矩阵允许公共自建样本debug日志，绑定EGL/VK选择与每个case。颜色API warning保留原返回码。NativeWindow元数据不做无界/竞态轮询。HDR→SDR→HDR与同transfer不同metadata在同实例观察；无法可靠回读则未测。
