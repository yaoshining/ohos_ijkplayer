#!/usr/bin/env python3
"""Extract the exact Phase28 parent-release-chain source slices.

The harness never re-authors production control flow.  Every function and the
two VOCTRL case bodies are copied verbatim from the selected mpv tree and
wrapped in #line directives so assertions and logs point at the real source.
A compile failure is never accepted as RED.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

UNITS = [
    ("video/out/hwdec/hwdec_ohcodec.c", "generic", [
        "static void on_frame_available(void *opaque)",
        "static void mapper_uninit(struct ra_hwdec_mapper *mapper)",
        "int ohcodec_mapper_drain(struct ra_hwdec_mapper *mapper, int reason,",
        "bool ohcodec_mapper_can_drain(struct ra_hwdec_mapper *mapper)",
        "bool ohcodec_mapper_surface_invalid(struct ra_hwdec_mapper *mapper)",
        "void ohcodec_mapper_mark_surface_invalid(struct ra_hwdec_mapper *mapper)",
        "bool ohcodec_hwdec_surface_invalid(struct ra_hwdec *hw)",
        "void ohcodec_hwdec_mark_surface_invalid(struct ra_hwdec *hw)",
        "struct ra_hwdec *ohcodec_hwdec_find(struct ra_hwdec **hwdecs, int num)",
    ]),
    ("video/out/gpu/hwdec.c", "gpu", [
        "void ra_hwdec_mapper_free(struct ra_hwdec_mapper **mapper)",
        "void ra_hwdec_mapper_unmap(struct ra_hwdec_mapper *mapper)",
        "void ra_hwdec_uninit(struct ra_hwdec *hwdec)",
        "void ra_hwdec_ctx_uninit(struct ra_hwdec_ctx *ctx)",
    ]),
    ("video/hwdec.c", "registry", [
        "struct mp_hwdec_devices *hwdec_devices_create(void)",
        "void hwdec_devices_destroy(struct mp_hwdec_devices *devs)",
        "void hwdec_devices_add(struct mp_hwdec_devices *devs, struct mp_hwdec_ctx *ctx)",
        "void hwdec_devices_remove(struct mp_hwdec_devices *devs, struct mp_hwdec_ctx *ctx)",
        "void hwdec_devices_set_loader(struct mp_hwdec_devices *devs,",
    ]),
    ("video/out/hwdec/hwdec_ohcodec_pl.c", "vk", [
        "static int64_t p27_monotonic_us(void)",
        "static int diagnostic_result(struct ra_hwdec_mapper *mapper,",
        "static int release_acquired_buffer(struct ra_hwdec_mapper *mapper,",
        "static int release_window_buffer(struct ra_hwdec_mapper *mapper, int fence_fd)",
        "static void destroy_import(struct ra_hwdec_mapper *mapper,",
        "static int ohcodec_drain(struct ra_hwdec_mapper *mapper, int reason,",
    ]),
    ("misc/dispatch.c", "dispatch", [
        "struct mp_dispatch_queue *mp_dispatch_create(void *ta_parent)",
        "void mp_dispatch_set_wakeup_fn(struct mp_dispatch_queue *queue,",
        "static void mp_dispatch_append(struct mp_dispatch_queue *queue,",
        "void mp_dispatch_run(struct mp_dispatch_queue *queue,",
        "void mp_dispatch_queue_process(struct mp_dispatch_queue *queue, double timeout)",
        "void mp_dispatch_interrupt(struct mp_dispatch_queue *queue)",
    ]),
    ("video/out/vo.c", "vo", [
        "void vo_ohcodec_retire_frames(struct vo *vo)",
        "static void run_control(void *p)",
        "int vo_control(struct vo *vo, int request, void *data)",
        "static void terminate_vo(void *p)",
        "static void dealloc_vo(struct vo *vo)",
        "void vo_destroy(struct vo *vo)",
        "static MP_THREAD_VOID vo_thread(void *ptr)",
    ]),
    ("player/video.c", "player_video", [
        "void uninit_video_out(struct MPContext *mpctx)",
    ]),
    ("player/main.c", "player_main", [
        "void mp_destroy(struct MPContext *mpctx)",
    ]),
    ("video/decode/vd_lavc.c", "vd", [
        "static bool ohcodec_lifecycle_enabled(vd_ffmpeg_ctx *ctx)",
        "static bool ohcodec_surface_query_enabled(vd_ffmpeg_ctx *ctx)",
        "static bool ohcodec_surface_invalid(vd_ffmpeg_ctx *ctx)",
        "static void ohcodec_mark_surface_invalid(vd_ffmpeg_ctx *ctx)",
        "static bool ohcodec_lifecycle_preflight(struct mp_filter *vd, int reason)",
        "static void reset_avctx_reason(struct mp_filter *vd, int reason)",
        "static void flush_all_reason(struct mp_filter *vd, int reason)",
        "static void uninit_avctx(struct mp_filter *vd)",
    ]),
    ("video/out/vo_gpu_next.c", "vo_gpu_next", [
        "static void uninit(struct vo *vo)",
    ]),
]

CASES = [
    ("video/out/vo_gpu_next.c", "gpu_control", "case VOCTRL_OHCODEC_SURFACE: {"),
    ("video/out/vo_gpu_next.c", "gpu_control", "case VOCTRL_OHCODEC_DRAIN: {"),
]


def find_body(s, marker):
    pattern = re.escape(marker).replace(r"\ ", r"\s+")
    matches = list(re.finditer(r"^" + pattern, s, re.M))
    defs = []
    for m in matches:
        j = m.end()
        while j < len(s) and s[j] in " \t\r\n":
            j += 1
        if j < len(s) and s[j] != ";":
            defs.append(m)
    if len(defs) != 1:
        raise ValueError("definition not unique: %r (%d)" % (marker, len(defs)))
    start = defs[0].start()
    i = s.index("{", start) + 1
    depth = 1
    while i < len(s):
        if s.startswith("//", i):
            j = s.find("\n", i)
            i = len(s) if j < 0 else j + 1
            continue
        if s.startswith("/*", i):
            j = s.find("*/", i + 2)
            i = len(s) if j < 0 else j + 2
            continue
        c = s[i]
        if c in "\"'":
            q = c
            i += 1
            while i < len(s):
                if s[i] == "\\":
                    i += 2
                    continue
                if s[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise ValueError("unterminated body: %r" % marker)


def find_case(s, marker):
    start = s.index(marker)
    brace = s.index("{", start)
    depth = 0
    i = brace
    while i < len(s):
        if s.startswith("//", i):
            j = s.find("\n", i)
            i = len(s) if j < 0 else j + 1
            continue
        if s.startswith("/*", i):
            j = s.find("*/", i + 2)
            i = len(s) if j < 0 else j + 2
            continue
        c = s[i]
        if c in "\"'":
            q = c
            i += 1
            while i < len(s):
                if s[i] == "\\":
                    i += 2
                    continue
                if s[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise ValueError("unterminated case: %r" % marker)


def extract(root, out):
    out.mkdir(parents=True, exist_ok=False)
    files = {}
    binding = {"mpvRoot": str(root), "kind": "parent-chain",
               "extraction": "exact source slices; no algorithm rewrites",
               "sources": []}
    for rel, tag, markers in UNITS:
        p = root / rel
        raw = p.read_bytes()
        s = raw.decode()
        chunks = []
        funcs = []
        for marker in markers:
            try:
                start, end = find_body(s, marker)
            except ValueError:
                # The terminal barrier is the Phase28 fix and is absent in RED.
                continue
            text = s[start:end]
            line = s[:start].count("\n") + 1
            chunks.append((line, '#line %d "%s"\n%s\n' % (line, rel, text)))
            funcs.append({"marker": marker, "startLine": line,
                          "endLine": s[:end].count("\n") + 1,
                          "sha256": hashlib.sha256(text.encode()).hexdigest()})
        if chunks:
            chunks.sort(key=lambda c: c[0])
            files[tag] = "\n".join(c[1] for c in chunks)
        binding["sources"].append({
            "path": rel,
            "sourceSHA256": hashlib.sha256(raw).hexdigest(),
            "functions": funcs,
        })
    cases = {}
    for rel, tag, marker in CASES:
        p = root / rel
        raw = p.read_bytes()
        s = raw.decode()
        start, end = find_case(s, marker)
        text = s[start:end]
        line = s[:start].count("\n") + 1
        cases.setdefault(tag, []).append((line, '#line %d "%s"\n%s\n' % (line, rel, text)))
        binding.setdefault("cases", []).append({
            "path": rel, "marker": marker, "startLine": line,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        })
    for tag, chunks in cases.items():
        chunks.sort(key=lambda c: c[0])
        files[tag] = "\n".join(c[1] for c in chunks)
    for tag, text in files.items():
        (out / ("actual-%s.inc" % tag)).write_text(text)
    all_text = "\n".join(files[k] for k in sorted(files))
    binding["extractedSHA256"] = hashlib.sha256(all_text.encode()).hexdigest()
    binding["terminalBarrierPresent"] = "ohcodec_terminal_barrier" in files.get("generic", "")
    (out / "source-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
    print("extracted", sum(len(x["functions"]) for x in binding["sources"]),
          "functions and", len(binding.get("cases", [])), "case bodies into", sorted(files))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mpv-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    extract(args.mpv_root.resolve(), args.out)


if __name__ == "__main__":
    main()
