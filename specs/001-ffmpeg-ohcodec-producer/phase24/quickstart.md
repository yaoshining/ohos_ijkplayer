# Phase24 验证入口
所有命令在producer根，Python使用-B和PYTHONDONTWRITEBYTECODE=1/PYTHONNOUSERSITE=1。
1. `python3 -B out/phase24/verify_boundary.py`，只写Phase24证据；确认旧封存。
2. `python3 -B -m unittest discover -s out/phase24/tests -v`；保存RED及GREEN，读取失败而非只看退出码。
3. 按out/phase24/tools的生成器在fixtures/hdr输出三类样本，验证已知像素+ffprobe，不用研究临时文件替代正式结果。
4. 用户确认外部凭据保存、电视连接后，指定NAS文件精确预检，不列目录。仅保存样本ID的公共元数据。
5. 在out/phase24/app用devecocli build/run，唯一目标设备；验证HAP绑定、实际maps，再短测，之后至少60分钟真实长播。期间不覆盖HAP。
6. HDR分项短矩阵和同实例切换，待画面稳定后人工观感/听音单列。
7. 最终复核边界和来源，隔离CI只选源码/规范/脱敏结果，任何缺口保留pending。
