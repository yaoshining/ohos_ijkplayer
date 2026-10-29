# Phase31 正常播放器操作与证据门禁

这组独立宿主测试核对正常组合的操作控制、实际ArkTS入口/关闭顺序和离线证据门禁。不会连接设备、读取NAS凭据或执行目标构建。播放器候选/HAR未替换，Player/TV保持只读，`formalArtifactAllowed=false`。

当前真机结论是七个短场景通过；60分钟NAS长播尝试01在788.048305秒有效窗口因真实后台事件中断，未通过。后台触发原因未确定：用户无法确认当时是否操作，不能归因用户、系统休眠或播放器崩溃。一次现场SDR声画观察不扩展为全程60分钟或HDR。后续重试必须独立连续计时。

## 当前库材料的权威边界

- `normal-library-binding.json`：本轮当前8个复用库。
- `target-artifact-manifest.json`：已在本地实际解包核验的HAP完整SHA、9库及源码索引声明。HAP没有上传，CI不重新读取其真实字节。
- `app/entry/src/main/cpp/expected.h`：实际编入包装库的7库运行时期望值，与当前清单相同。
- **`app/lib-binding.json`是历史继承的Phase28元数据，保留原始目标源码快照，不是本轮权威清单。** 它的旧SHA与本轮真实库不同，不得用于当前库判断。
- `binding-policy.json`明确此区别；`verify_current_binding.py`核验当前键集合/哈希、HAP声明、实际expected.h、源码快照及历史文件的溯源SHA，禁止把历史元数据切换为当前来源。

旧attempt01封存及构建源冻结均未更改。CI中的app目录是目标源码文本快照；没有随附音视频、字体、图片、库或签名，不能作为可部署工程。

## 本地执行

从精确提交的clean checkout执行：

```sh
python3 -B tools/phase31-normal-validation/runner.py --out /tmp/phase31-evidence
```

输出必须是仓库外新目录。入口验证源码索引和工作流/Spec Kit的外部哈希，执行C++实际头/控制器、ArkTS实际方法切片、离线门禁与当前库材料绑定测试。TypeScript通过锁文件安装，禁用install scripts。输出目录中的artifact只有UTF-8文本，失败日志同样收集。

本地开发使用`--allow-dirty`只能算预演，不能称精确提交重放。远端Linux CI、本地macOS重放、目标HAP构建与真机验收分别声明。

夹具类型和本地原始证据重放说明见`tests/fixtures/README.md`。CI输入没有原始设备日志、私人影片路径或凭据。
