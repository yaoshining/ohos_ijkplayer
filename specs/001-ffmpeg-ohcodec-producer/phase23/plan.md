# Phase23 实施计划

技术：C/C++、ArkTS独立HAP、Python编排、固定OHOS AArch64工具链、devecocli。官方setup-plan已执行，使用SPECIFY_FEATURE_DIRECTORY和NO_PERSIST=1，不改业务分支和feature指针。

源码与产物放out/phase23/input-package/sources、ffmpeg-input/source、build、app、tools、tests；文档在本目录。旧Phase22/03只读。先封存前置基线，分SMB/GPU两项只读研究，主代理唯一设备操作者。

US1先定位FFmpeg前置、smbc_open、Samba连接/认证/文件层。仅增加脱敏stage/errno/NTSTATUS；如果是夹具/端口接线则修调用合同，不无依据改库；确有库缺陷再复制固定源码补丁重建。

US2分固定与新Surface循环，至少3轮热身+10轮稳定期，每轮观察销毁和延迟回收，并保留无播放器对照。先查所有权合同，禁止盲目补Destroy导致重复释放。定位后只修责任层。

US3旧默认GL为RED、应用强制RGBA8为对照；库的窗口上下文负责格式选择/恢复，应用取消代设后复测。

新库构建前绑定来源及工具链，依赖只读复核摘要，受影响库双clean比较；maps绑定实际新库。宿主回归、目标编译、真机、CI分别报告。新推送授权单独判断。

宪章检查：新直接人类授权覆盖修复及指定设备；Player/TV只读、候选不替换、旧证据不覆盖、Python和默认生成器保持、不读keys内容。保留RED/GREEN和failed/blocked/untested。正式产物资格false。签名沿用官方流程，HAP含临时凭据只留本地。

研究假设由真实源码/设备实验判定，研究完进入实施，不以方案交付结束。先US1和US2，再US3；不同源码调查可并行，设备实验串行。
