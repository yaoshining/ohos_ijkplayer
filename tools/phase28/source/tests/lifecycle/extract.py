#!/usr/bin/env python3
"""Extract exact lifecycle functions from baseline or Phase28 mpv slices.

No algorithm is rewritten. Only source slices are copied. The two static
functions both called `mapper_uninit` live in different translation units and
are emitted into separate include files so the harness can rename one via the
preprocessor without text substitution.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("PHASE28_BINDING_ROOT", str(HERE.parents[3])))
BASELINE = Path(os.environ.get("PHASE28_BASELINE_ROOT", str(ROOT / "out/phase28/baseline")))
PHASE28_MPV = Path(os.environ.get("PHASE28_MPV_ROOT", str(ROOT / "out/phase28/input-package/sources/mpv")))
PHASE28_FFMPEG = Path(os.environ.get("PHASE28_FFMPEG_ROOT", str(ROOT / "out/phase28/ffmpeg-input/source")))

ROOTS = {
    "baseline": {"mpv": BASELINE / "mpv", "ffmpeg": BASELINE / "ffmpeg"},
    "phase28": {"mpv": PHASE28_MPV, "ffmpeg": PHASE28_FFMPEG},
}

UNITS = {
    "mpv": [
        ("video/out/hwdec/hwdec_ohcodec.c", "generic", [
            "static int mapper_init(struct ra_hwdec_mapper *mapper)",
            "static void mapper_uninit(struct ra_hwdec_mapper *mapper)",
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
        ]),
        ("video/out/hwdec/hwdec_ohcodec_pl.c", "vk", [
            "static int64_t p27_monotonic_us(void)",
            "static int release_acquired_buffer(struct ra_hwdec_mapper *mapper,",
            "static void release_acquired_buffer(struct ra_hwdec_mapper *mapper,",
            "static int release_window_buffer(struct ra_hwdec_mapper *mapper, int fence_fd)",
            "static void release_window_buffer(struct ra_hwdec_mapper *mapper, int fence_fd)",
            "static void mapper_release(struct ra_hwdec_mapper *mapper)",
            "static void mapper_uninit(struct ra_hwdec_mapper *mapper)",
            "static int ohcodec_drain(struct ra_hwdec_mapper *mapper, int reason, int *platform_error)",
        ]),
        ("video/decode/vd_lavc.c", "vd", [
            "static void reset_avctx(struct mp_filter *vd)",
            "static void reset_avctx_reason(struct mp_filter *vd, int reason)",
            "static void flush_all(struct mp_filter *vd)",
            "static void flush_all_reason(struct mp_filter *vd, int reason)",
            "static void uninit_avctx(struct mp_filter *vd)",
            "static int send_packet(struct mp_filter *vd, struct demux_packet *pkt)",
            "static int decode_frame(struct mp_filter *vd)",
            "static bool ohcodec_lifecycle_preflight(struct mp_filter *vd, int reason)",
            "static bool ohcodec_lifecycle_enabled(vd_ffmpeg_ctx *ctx)",
            "static bool ohcodec_surface_query_enabled(vd_ffmpeg_ctx *ctx)",
            "static bool ohcodec_surface_invalid(vd_ffmpeg_ctx *ctx)",
            "static void ohcodec_mark_surface_invalid(vd_ffmpeg_ctx *ctx)",
            "static bool ohcodec_lifecycle_refuse_init(vd_ffmpeg_ctx *ctx)",
        ]),
        ("video/out/vo.c", "vo", [
            "void vo_ohcodec_retire_frames(struct vo *vo)",
            "static void run_control(void *p)",
            "int vo_control(struct vo *vo, int request, void *data)",
            "void vo_seek_reset(struct vo *vo)",
        ]),
    ],
    "ffmpeg": [
        ("libavcodec/ohdec.c", "ohdec", [
            "static OHCodecDecRef *oh_decode_ref(const OHCodecDecContext *s)",
            "static bool oh_decode_admit(OHCodecDecRef *ref, AVCodecContext **out)",
            "static void oh_decode_end(OHCodecDecRef *ref)",
            "static void oh_decode_report_error(OHCodecDecContext *s, int32_t err)",
            "static uint64_t oh_decode_generation(const OHCodecDecContext *s)",
            "static void oh_decode_invalidate_outputs(OHCodecDecContext *s)",
            "static void oh_decode_release(void *opaque, uint8_t *data)",
            "static int oh_decode_create(OHCodecDecContext *s, AVCodecContext *avctx)",
            "static void oh_decode_on_err(OH_AVCodec *codec, int32_t err, void *userdata)",
            "static int oh_decode_apply_stream_changed(OHCodecDecContext *s,",
            "static void oh_decode_on_stream_changed(OH_AVCodec *codec, OH_AVFormat *format,",
            "static void oh_decode_on_need_input(OH_AVCodec *codec, uint32_t index,",
            "static void oh_decode_on_output(OH_AVCodec *codec, uint32_t index,",
            "static int oh_decode_start(OHCodecDecContext *s, AVCodecContext *avctx)",
            "static av_cold int oh_decode_close(AVCodecContext *avctx)",
            "int av_ohcodec_release_buffer(AVOHCodecBuffer *buffer, int render)",
            "static void oh_buffer_release(void *opaque, uint8_t *data)",
            "static void oh_decode_discard_output(OHCodecDecContext *s,",
            "static int oh_decode_send_pkt(AVCodecContext *avctx,",
            "static void oh_decode_flush(AVCodecContext *avctx)",
        ]),
    ],
}


def find_body(s, marker):
    pattern = re.escape(marker).replace(r"\ ", r"\s+")
    matches = list(re.finditer(r"^" + pattern, s, re.M))
    # A prototype and its definition can both match. Keep only matches whose
    # next non-space character is the function body opener.
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


def extract(source, kind):
    root = ROOTS[source]
    manifest = []
    files = {}
    for relative, tag, markers in UNITS[kind]:
        p = root[kind] / relative
        raw = p.read_bytes()
        s = raw.decode()
        items = []
        chunks = []
        for marker in markers:
            try:
                start, end = find_body(s, marker)
            except ValueError:
                # Optional Phase28-only helpers legitimately do not exist in baseline.
                continue
            text = s[start:end]
            line = s[:start].count("\n") + 1
            chunks.append((line, '#line %d "%s"\n%s\n' % (line, relative, text)))
            items.append({
                "marker": marker,
                "startLine": line,
                "endLine": s[:end].count("\n") + 1,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
        if chunks:
            chunks.sort(key=lambda c: c[0])
            files[tag] = "\n".join(c[1] for c in chunks)
        manifest.append({
            "source": os.path.relpath(p, ROOT),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "functions": items,
        })
    all_text = "\n".join(files[k] for k in sorted(files))
    binding = {
        "source": source,
        "kind": kind,
        "extraction": "exact source slices; no algorithm rewrites",
        "sources": manifest,
        "extractedSHA256": hashlib.sha256(all_text.encode()).hexdigest(),
    }
    return files, binding


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["baseline", "phase28"], required=True)
    ap.add_argument("--kind", choices=["mpv", "ffmpeg"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    files, binding = extract(args.source, args.kind)
    for tag, text in files.items():
        (out / ("actual-%s.inc" % tag)).write_text(text)
    (out / "source-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
    print("extracted", sum(len(x["functions"]) for x in binding["sources"]),
          "functions into", sorted(files))


if __name__ == "__main__":
    main()
