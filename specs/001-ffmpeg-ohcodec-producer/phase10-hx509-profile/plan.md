# Phase10 实施计划

现有feature增量；使用官方SPECIFY_FEATURE_DIRECTORY与NO_PERSIST，不改旧工件/feature指针。先任务与analyze，再实施。无runtime API实现。

新增tools/hx509-history/：profile.py提供显式选择、独立source锁/工具构建、真实Waf两个任务级env派生和输出门禁；run.py负责复制冻结默认recipe到新目录、仅给副本添加profile钩子、预锁并调用既有依赖/SDK构建程序；tests/真实回归；boundary/宿主C harness与运行器；ci.sh/独立工作流负责Linux opt-in。默认tools/ffmpeg8和既有workflow文件不写。

选择实现：在全新Samba目标树内，为bison task的sel-gram.y和Samba实际samba_waf18.flexfun的sel-lex.l派生私有env，覆盖该task工具/参数/BISON_PKGDATADIR；其他输入和host compile_et/asn1工具保持原配方。对Waf模块/语法摘要做失败关闭的补丁锚定，保存补丁，执行时预后校验历史工具/资源。新增来源只写tools/hx509-history/sources.lock.json。

每个平台两次clean先各建历史工具，再全八依赖。对八库进行重复比较后，各自对应依赖构建FFmpeg以检验配对链；若需要区分prefix/配置元数据影响，可另以同一固定静态root重复FFmpeg，必须说明层次。macOS使用已固定API24 NDK；Linux使用既有固定Debian镜像/签名snapshot及OpenHarmony5.0 NDK，实际GitHub CI执行与下载复核。默认workflow继续原行为，新增工作流仅显式触发；若平台限制需分支专用workflow配置，保留默认值/流程，并记录具体变更。

边界harness编译未改的生成C，提供最小hx_locl声明和构造/错误回调；用真实token/parse返回值判断，malloc/realloc故障注入不替换生成逻辑。短输入、长标识符、quoted string、未闭合字符串、深括号、lex缓冲扩容和SIZE_MAX边界均独立子进程并设超时。ASan/UBSan异常保留为finding，历史与当前对照；发现固有缺陷时不以历史字节对齐为由修改默认源码，也不将“成功捕获失败”表述为解析通过。

完整哈希分析复用只读ELF审计和控制链接方法，所有新输出out/phase10；单项历史置换与新源码修改分别命名，记录输入摘要/实际选入成员。先控制组全字节复现本轮，再做version、GnuTLS、Samba项消元。必要时明确剩余未归因，禁止为全等恢复宿主Python路径。

宪章I–V检查：职责/冻结、TV字节优先、TDD、来源闭包分层、设备/发布状态均保留。业务checkout不切分支；为CI使用独立codex/分支和隔离index；不合并发布。

Resume-01 最小补充：profile.py 对已预锁的 M4 查询实际版本，只接受已实测的 1.4.6/1.4.19，并生成严格全文摘要期望及版本记录；run.py 在构建前记录版本，apply 时复验工具摘要。测试用原始生成 fixture 覆盖两套接受、跨套拒绝、输出改动拒绝和未知版本拒绝。独立相同 NDK 编译用于证明注释差不改变目标对象，实际 CI 仍须两次 fresh。无生成文件后处理、默认生成器或运行目录 API 变更。
