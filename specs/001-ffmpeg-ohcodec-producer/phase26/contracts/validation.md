# 验证合同

CI：冻结文件必须摘要一致，缺失/漂移失败；子进程失败原码传播；显式允许源码和本轮已登记日志进入 artifact，哨兵 credentials.json/nas.bin/private/*.hap 不收集。源代码产物与运行结果独立。
HDR：所有权按 acquire→read→release 串行；只首帧 render；失败归还已有引用/fence，callback 仅通知。AVFrame side data 做size检查、复制数值；MDM/CLL缺失明确 present=false。外部停止不强杀正在调用库的线程；deadline有限接收循环，永久调用阻塞不宣称可取消。
应用：仅 setWindowKeepScreenOn，退出false读回。新 HAP 绑定原七库、源码和原创夹具；不包含用户凭据。原始日志只留本地。
