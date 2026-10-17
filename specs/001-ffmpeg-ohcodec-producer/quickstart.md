# 操作入口

先执行 `python3 -m unittest discover -s tools/ffmpeg8/tests -p 'test_*.py' -v` 和 `bash tools/ffmpeg8/tests/test-sdk-contract.sh`。具体导入、构建、核验命令与输入路径见 tools/ffmpeg8/README_zh.md。输出必须新目录，禁止覆盖 TV 或旧 SDK。最终跨会话入口为 docs/vidall-tv-baseline-handoff.json。
