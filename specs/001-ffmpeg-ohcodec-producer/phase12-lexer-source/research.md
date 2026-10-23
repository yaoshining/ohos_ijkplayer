# 方案依据与决策

## 决策：分开 HX509 与剩余 lexer

原因：`docs/producer-phase9-source-report.md` 已证明固定 GNU Bison 2.3 + Apple bison-16 data、Apple flex-35 能复现 HX509；Phase11 的剩余对象为另一生成任务 `lex.lex.c.124.o`。其历史 C SHA 为 `4815000afa455ee8fb5b8fc85b4c6172402adc84798ef8d1690ed781b090b549`，对象 SHA 为 `6eb055d999f8936b71e5dab8660f052c2c0c1ebaa25ac061fedcdad1a4a86918`。

替代方案：全局切换旧生成器或扩大 HX509 特例均缺乏证据，不采用。

## 决策：先来源排除，再实际重建

Phase11 的官方 Flex 2.6.4 与当前 Xcode 对照均不匹配历史 C/对象；Bison parse.tab.c/h 已匹配。历史 yyleng、yy_n_chars、yy_scan_bytes 长度用 yy_size_t，yy_buf_size 为 int，不能仅凭 2.6.4 标识确定来源。进一步只读 upstream/发行版调查保存在 `out/phase12/upstream-research`，属于新增研究，不计成功生成或已证明历史安装身份。

替代方案：反向编辑生成 C、拼凑未见于来源的补丁、历史对象回填均排除。来源未找到时输出具体已排除范围和检索缺口。

## 决策：保留 Python 修复与运行接口分离

Phase11 的实际 ELF 指针证据表明 TV 含宿主 Python 路径；当前目标路径修复使完整 TV SHA 无法同时保持。目标 Python 目录是禁用 Python 的构建元数据，不应据此新增 mkdir 或启用 Python。运行目录显式配置会改变初始化行为，需要单独合同和实现授权阶段，不塞入来源诊断。

研究没有新的产品偏好问题；剩余来源身份必须靠实验验证，不能作为默认工具修改依据。

## 本轮新增排除证据

只读研究已完成快照：`out/phase12/upstream-research/report.md`、`matrix.json`、`inventory.json`。实际固定源码显示 upstream 2.6.0–2.6.4 五个正式标签所核验的骨架均不具备历史完整类型组合；官方主线先把 yy_n_chars 改 int，之后才把 yy_buf_size 改 int，不能通过选取该区间的中间提交得到历史反向组合。当前固定 Homebrew 配方仅有 configure/libtool 补丁，Debian 2.6.4-8.2 原补丁也不改变关键类型。Homebrew 历史 API 返回 500，不能排除全部历史配方；Apple、Android/ANGLE 精确下游来源仍需继续调查。本轮未构建/生成/编译。

限制：五个标签的静态骨架特征不等于五套发行工具都已重建。若归档使用预生成 skel.c/scan.c，必须固定并核验实际编译输入，不能只依 flex.skl 推断输出。

## 后续实施结果与纠错

按20:15直接人类授权继续后，Apple固定revision 8548f53e24244c0a411dea128a21686b61d29df4 原包全新构建成功，实际版本2.6.4；flex-35只是发行标签，先前将其解释为2.5.35的排除错误。全新工具生成C/目标对象均匹配历史，无补丁追加。source-verification.json记录正式门禁结果；独立归档/链接继续保留Python修复，最终仍不等TV。详见 docs/producer-phase12-report.md。上文未知来源是早期研究快照，不是最终结论。
