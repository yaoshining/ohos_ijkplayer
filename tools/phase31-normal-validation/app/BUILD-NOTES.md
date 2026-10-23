# Phase28 诊断应用构建说明

本目录只保留应用源码、固定库和 `private/phase28-diagnostic.hap`。为避免把签名材料或 hvigor 缓存写入证据目录，以下内容未随包保存：

- `build-profile.json5`：构建时临时软链到用户私有 Phase27 工程配置（只读），未复制其内容。
- `.hvigor/`、`entry/build/`、`entry/.cxx/`、`hvigor-home/`：可重建状态与可能含签名命令的缓存。

重建方式（需用户私有签名配置）：

```sh
cd out/phase28/app
HOME=<isolated writable home> DEVECO_SDK_HOME=/Applications/DevEco-Studio.app/Contents/sdk \
  /Applications/DevEco-Studio.app/Contents/tools/hvigor/bin/hvigorw \
  --mode module -p product=default assembleHap --no-daemon
```

产物 HAP 已另存为 `private/phase28-diagnostic.hap`（0600），其内 `libmpv.so` 与 `libavcodec.so.62` SHA256 见 `../build/evidence-final.json`。
