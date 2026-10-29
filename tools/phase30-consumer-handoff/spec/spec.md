# 同一 consumer 交接与真实并发验证

用户要求优先补齐同consumer交接和强并发真机验证，沿用Spec Kit/TDD；root负责审查。起点为已批准6520a29及两个完整封存。本轮Player/TV只读、不替换候选/HAR/默认SDK、不改系统设置，只操作独立诊断应用；formalArtifactAllowed=false。

## 范围

A：单个mpv实例，在force-window=yes的独立场景中完成至少两次旧decoder→新decoder交接。证据必须证明同一持久owner实例/consumer代次、NativeImage和其Surface ID持续存在，NativeWindow查询ID与其相同；展示Surface ID和地址复用均不足。

B：在同一mpv实例真实normal链中，平台callback已经通过真实oh_decode_admit且active>0，真实Close/Flush进入等待；另两线程真实提交请求（至少一条loadfile），证明请求/等待与callback及关闭发生实际重叠。通过事件确认后释放callback屏障，观察真实Stop/Destroy返回之后才有新decoder的SetSurface。记录实际线程ID、单调事件序号、实例和代次，不能用串行循环或sleep制造交错结论。

不新增consumer registry/producer拒绝锁来替代产品已有同步；旧consumer-challenge只是一条同线程registry自测，不纳入本轮强并发验收。不声称任意两个mpv实例或外部直接decoder共享consumer的安全保证。若现有normal链缺少所需保证或A仍重建consumer，先报告root，不篡改验收条件。

## 成功与异常契约

同一consumer的序列须满足：A drain SAFE结束 → A Stop返回0 → A Destroy返回0 → B SetSurface begin/end0 → B Start返回0。owner创建/销毁代次和consumer稳定ID贯穿；每个producer必须至少映射一帧。正常替帧保持原有异步行为，不新增逐帧GPU等待。

强并发屏障必须有held/close-wait/request-enter/释放/完成事件，三个以上真实线程ID；每阶段5秒有界等待，场景最长120秒，异常停止新的请求并释放测试屏障，必要时外部独立进程清理。屏障不会拒绝producer，也不会伪造平台返回值；库normal UNSAFE接管及应用3秒终止策略保持。

SAFE_RELEASE_ERROR/UNSAFE/Stop或Destroy失败的已有拒绝/保留策略作为真实函数回归；若设备未注入相应新场景保持待验收，不从宿主测试推导设备通过。

真实GPU调用永久不返回、物理HDR/主观声画、跨实例强并发和既有其他待验项目不在本轮自动验收范围。
