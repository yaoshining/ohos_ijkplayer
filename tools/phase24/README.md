# Phase24 诊断与验收合同

仅包含主机可测源代码、独立诊断应用源码、规范及脱敏证据；不含七库/HAP/签名/凭据/私人影片。CI成功只代表合同测试，不等同真机、HDR显示或60分钟NAS验收。

执行：`python3 -B -m unittest discover -s tools/phase24/tests -v`。

实际诊断使用原Phase23七库。10bit SDR/PQ/HLG已完成第一轮矩阵；HDR10硬解静态元数据缺口详见HDR-METADATA-FINDING.md，尚未修复。指定NAS长播等待用户确认私有认证配置保存，不能用短图案替代。
