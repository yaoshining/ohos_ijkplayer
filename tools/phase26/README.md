# Phase26 宿主诊断 CI

从封存 Phase25 按 sources.json 逐字节复制真实源码，不包含库、HAP、SDK、签名、凭据、媒体或设备日志。保留公共 mpv client.h 声明。设备接线源码随附供审阅，ciCompiled=false 的文件不由宿主构建。

运行：`PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 python3 -B tools/phase26/runner.py --output out/phase26-ci`。输出目录必须不存在；缺输入、摘要漂移、测试或原生程序失败均返回非零。artifact仅收集来源允许列表、已登记日志、运行记录与索引。

覆盖：Phase25原有13时间线+3电源Python测试；真实phase25_timeline.h的线程/阻塞/返回码/写入故障/生命周期ASan+UBSan；phase25_mpv.h和sampling.cpp实际包装函数的stub-link新增覆盖。stub只提供mpv API返回，不能证明硬件mpv行为。8项新runner/收集边界测试。

Linux启用ASan leak检测；macOS本地ASan不支持该模式，明确detect_leaks=0。未关闭address或undefined sanitizer。断言保持开启。原生合同日志含故意异常，不作为正常播放通过证据。

本轮真实RED在实现前缺runner导入；首次最小实现又因macOS /var 系统软链接误拒临时目录失败，限定源码根内的symlink检查后GREEN。旧Phase25 RED未改写。LinuxCI必须绑定新精确提交、实际run和下载制品；本地GREEN不等于CI已执行。targetExecutedByCI=false、HDRComplete=false、formalArtifactAllowed=false。

新增绑定回归：实际执行源码/工作流/规格逐项SHA与HEAD核对，GitHub run/attempt/SHA和工作树状态入记录；testsPassed与collectionComplete分开，收集失败总体failed。两项回归先观察缺失函数RED后实现GREEN。
