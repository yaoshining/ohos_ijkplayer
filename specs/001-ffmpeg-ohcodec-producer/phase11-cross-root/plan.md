# Phase11实施计划

技术上下文：现有bash/Python producer、固定FFmpeg8源码、macOS API24及Linux OpenHarmony5.0 NDK、现有独立HX509历史配置。默认生成器不切换，修复构建路径身份不改变目标功能。无外部API新增。

设计：在每个FFmpeg build目录创建deps/toolchain两个本地软链，分别指向该链已锁定的真实静态sysroot和NDK；configure argv、pkg-config搜索及头/库选取用同名相对入口。源链接继续使用src。helper校验输入存在、相对入口不被预占并记录resolvedPath；producer在调用前后复核输入且把实际绑定记录纳入SDK evidence。禁止全局固定根、输出后文本替换或借用另一链对象。

实施先写真实shell/clang/pkg-config回归：不同长度和空格路径仍能解析指定头/库，缺失/已有错误入口拒绝，实际源码编译出的配置字符串跨根原文相同。再针对完整FFmpeg configure执行小范围验证，随后两fresh全链。FFmpeg之外的旧依赖脚本若不支持空格根，须如实界定并先报告，不能用变更字符串长度掩盖。

新增phase11 runner/CI入口复用已锁定生成器与依赖构建逻辑，强制paired allMatch=true，不接受fixed-root作为替代；保持旧phase10脚本/证据可复验。优先新增tools/cross-root-profile，必要producer构建路径修复前归档旧字节。源/工具/依赖/NDK pin仍绑定物理输入，逻辑路径和物理路径分别表示。

源码调查按Spec plan研究步骤委派只读子任务：检查当前TV ELF路径与精确源码控制，输出独立source-research；若历史字节与目标Python配置冲突，证据先报，保持修复。旧version/GnuTLS/runtime/归档控制不称源码产物；可重建的单对象绑定源码/命令/完整SHA。未知项以证据缺口结束，不制造来源证明。

宪章I–V：无跨仓写入、无keys/部署/候选替换；TDD、来源分层和设备pending保留。上轮19052条及旧producer文件改变均有归档映射。本轮用户已授权同仓专用诊断CI推送；业务checkout/index保持。无extensions.yml，无checklists。
