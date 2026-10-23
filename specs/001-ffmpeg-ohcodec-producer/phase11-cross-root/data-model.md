# 数据模型

BuildInputBinding：role(deps/toolchain)、logicalPath、physicalPath、resolvedPath、输入manifest SHA；每次新build私有。入口创建前不存在；执行后仍解析同一输入。

CleanIteration：独立source/work/sysroot/generators/SDK，锁和实际文件摘要、构建命令、完成状态。只有成功构建及输入后验成立才参与重复性验收。

CrossRootComparison：两条不同真实目录，八静态库及六库/headers/pc原始SHA；不得共享实际工作树或对象，pairedAllMatch必须true。

SourceAlignmentFinding：目标TV SHA、源码锁与补丁、实际命令、源生对象SHA、historicalBinaryUsed=false、冲突/缺证；历史二进制仅放reference字段。
