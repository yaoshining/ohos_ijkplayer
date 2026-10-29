#!/usr/bin/env bash
# 容器挂载目录的 uid 与执行用户可能不同；仅给明确的当前仓库设置进程级信任。
lock_git_repository() {
  export GIT_CONFIG_COUNT=1
  export GIT_CONFIG_KEY_0=safe.directory
  export GIT_CONFIG_VALUE_0
  GIT_CONFIG_VALUE_0=$(cd -- "$1" && pwd -P)
}
