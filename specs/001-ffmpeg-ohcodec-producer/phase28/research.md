# Phase28 研究决策

研究依据：out/phase28/research/{codec-lifetime,gpu-lifetime,build-scope}/design.md，以及 gpu-lifetime/drain-interface.md；这些报告含实际源 hash。辅助元数据存在两处旧值：fresh_build.py bundle 摘要与 CI patchBytes，实际最终输入绑定正确，本轮重锁，旧封存不改。

- 决策：正常 Close 保留 Stop，但先同步 consumer drain。理由：last_src unref 可能发生在新 producer 接入后，且 release fence 提交不是完成。替代方案“最终引用 Stop”不足。
- 决策：preflight 在 mpv 的 void FFmpeg API 前。理由：ff_codec_close 不检查 codec->close 返回，free_context 继续释放；不增加无效的隐式失败 callback ABI。
- 决策：稳定 callback 主体 + admission/drain。四入口都受保护，内部 report_error/apply_format 拆分，避免嵌套 gate 和同步 fallback 混用 userdata。
- 决策：采用官方非 callback 线程调用成功返回前 callback 收尾契约。固定文档提交 15e95293641bf9e94e7ef4e12c3b2e93c263ef1b，raw 文件及 hash 在 out/phase28/research/official/source.json。它不是商用固件同源证明，也不为错误返回背书。
- 决策：仅 OHCodec Vulkan gpu-next 具有 drain 能力，GL 原逻辑作为对照。GL single-buffer API 不能套到当前普通 NativeImage。
- 决策：普通 EOF 延后 reset；正常替帧不等待队列全空。只有真正生命周期变化触发 barrier。
- 决策：GPU 完成未知的诊断 fail-stop 只在显式实验构建启用，并由独立 watchdog 验证；不引入通用 mpv 默认 abort。没有平台恢复证据时，不声称产品可恢复。

未完成的证据：真实函数 RED/GREEN、新构建、新 CI、设备实际队列和同 Surface 时序。以上均作为执行任务，不以研究结论替代验收。直接 FFmpeg consumer 需要自己先完成 GPU 并归还 buffer；本轮不承诺自动修复任意客户端错序调用。

补充审查决策：FR28-02 要求旧平台 Destroy 也在新 SetSurface 前完成。因此放弃研究草案中 final-reference Destroy；Close 先 drain/generation invalidation，再 Stop/Destroy，将 ref->dec 清空。散落旧 token 保留稳定壳，释放/重复 render 只返回失效状态，不能触发晚到平台操作。token native API 与 callback 共用 active admission 计数，Close 等待已进入操作，防 generation 检查与 native 调用之间的竞态。
