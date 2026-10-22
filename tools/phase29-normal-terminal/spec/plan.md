# 实施计划

1. 旧封存/保护边界核验，官方Spec Kit NO_PERSIST初始化与分析。
2. 先写C/C++动态链接测试，观察现有库缺少公共符号；真实语义RED仍保留上一阶段normal父链。补接口参数/大小/版本/重入/失败重试测试再实现最小wrapper。
3. wrapper只做验证、固定记录适配与原有terminal manager调用；新增include/mpv/ohcodec_terminal.h，四个导出符号，扩展版本1.0，不改核心2.5。
4. 新输入清单绑定源/补丁/工具链，正式normal两次clean；导出符号及C/C++ARM64链接验证。
5. 独立应用引入进程寿命native adapter与UI定时器，deadline不依赖事件回调；先测试adapter再改独立app。普通正常结束保持可再次播放。
6. 测试注入库单独来源包与身份，通过真实返回替换触发现有normal策略；不等同真实GPU故障。运行前确认独立bundle/签名，所有设备清理用既有加强门禁。
7. root审查，精确文本提交预览；不推送。
