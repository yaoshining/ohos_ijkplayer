# 历史 lexer 来源诊断

独立核验器，不修改默认 Bison/Flex、Samba 配方、候选或消费端。来源记录绑定固定归档/完整 Git revision/原补丁、实际骨架构建输入及构建工具；生成记录绑定实际 Flex/M4、输入和原始 stdout，核验真实 Waf UTF-8 解码、通用换行、latin-1 写出后的 C；编译记录绑定编译器/头文件/生成 C/命令/对象。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tools/lexer-source-profile/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/lexer-source-profile/profile.py /absolute/record.json --output /absolute/result.json --require-match
```

`--require-match` 在原始 C 或完整对象不等时返回 2；缺少来源、输入漂移、失败命令或输出被改写返回 1。未加此开关可保存有效排除结果。特征相同不代表完整输出相同；Apple 发行标签不推断上游版本，SIZE_MAX 常量定义也不等于扩容保护分支。

记录结构与约束见相邻 tests/test_profile.py 的合成夹具及 feature 的 data-model.md。夹具不是真实来源复现证据。核验器检查文件/记录自洽性，不能独立认证日志真实性、历史机器安装身份或完整宿主依赖闭包。实际构建必须另行记录真实执行与预后摘要。生成器预生成 skel.c 和 flex.skl 都需绑定，以实际编译输入为准。任何成功均不授予正式产物/设备验收。

本轮实际复现和 CI 结果见 docs/producer-phase12-report.md（完成交接时生成）。
