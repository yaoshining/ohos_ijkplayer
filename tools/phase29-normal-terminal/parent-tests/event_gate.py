import re
# 复用已审查 F1 完整事件门禁，来源 run.py；非计数缺失默认零。
FORBIDDEN_EVENTS = [
    "EVENT destroy-queue", "EVENT destroy-registry",
    "EVENT destroy-gpu-ctx", "EVENT destroy-renderer",
    "EVENT destroy-texture", "EVENT destroy-options",
    "EVENT destroy-cache", "EVENT destroy-icc", "EVENT destroy-lut",
    "EVENT destroy-shader", "EVENT avctx-free", "EVENT mapper-free",
    "EVENT owner-free", "EVENT vk-mapper-free", "EVENT parent-vo-free",
    "EVENT parent-mpctx-free", "EVENT parent-mconfig-free",
    "EVENT parent-abort-list-free", "EVENT parent-osd-free",
    "EVENT parent-input-free", "EVENT parent-clipboard-free",
    "EVENT parent-global-free", "EVENT parent-clients-free",
    "EVENT parent-command-free", "EVENT parent-encoder-free",
    "EVENT parent-log-free", "EVENT uninit-end", "EVENT dr_helper-free",
    "EVENT core-after-mp-destroy", "EVENT all-done",
]
PREFLIGHT_ONLY_FORBIDDEN = [
    "EVENT parent-ipc-free", "EVENT parent-audio-out-free",
    "EVENT video-chain-uninit", "EVENT uninit-begin",
]


def destroy_events(stdout):
    return [x for x in FORBIDDEN_EVENTS if x in stdout]


def observer_destroy_events(stdout):
    vals = re.findall(r"EVENT observer-snapshot destroy_events=(\d+)", stdout)
    return [int(x) for x in vals]


def forbidden_events(stdout, case):
    bad = destroy_events(stdout)
    if case != "late-unsafe":
        bad += [x for x in PREFLIGHT_ONLY_FORBIDDEN if x in stdout]
    # late-unsafe legitimately performs pre-VO mp_destroy steps; its critical
    # events are checked explicitly above.  The observer snapshot is a second
    # check for paths that must have zero destroys at all.
    if case != "late-unsafe" and any(v > 0 for v in observer_destroy_events(stdout)):
        bad.append("observer-snapshot destroy_events>0")
    return bad
