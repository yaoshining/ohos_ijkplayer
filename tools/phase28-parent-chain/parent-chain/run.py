#!/usr/bin/env python3
"""Run the Phase28 real parent-release-chain harness.

RED (current source): the exact hwdec_devices_destroy assertion after the
queue/parent teardown starts.  GREEN (fixed source): the terminal barrier line
with no destruction events, plus normal/SAFE_RELEASE_ERROR cleanup and a
barrier-removed negative control that still releases the parent tree.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_process(cmd, timeout, env):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, env=env)
    timed_out = False
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        alive = p.poll() is None
        p.kill()
        stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr, timed_out, alive
    return p.returncode, stdout, stderr, timed_out, False


def parse_counts(stdout):
    m = re.search(r"EVENT counts (.+)", stdout)
    if not m:
        return {}
    return dict(re.findall(r"(\w+)=(-?\d+)", m.group(1)))


def parse_parent_counts(stdout):
    m = re.search(r"EVENT parent_counts (.+)", stdout)
    if not m:
        return {}
    return dict(re.findall(r"(\w+)=(-?\d+)", m.group(1)))


CRITICAL_PARENT = ["mpctx_free", "mconfig_free", "abort_list_free",
                   "osd_free", "input_free", "clipboard_free",
                   "global_free", "clients_free", "command_free",
                   "encoder_free", "msg_uninit"]
CORE_DESTROY = ["queue_destroy", "registry_destroy", "gpu_ctx_destroy",
                "dr_helper_free", "parent_vo_free", "parent_other_free"]
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


def zero(values, keys):
    # A barrier process is killed before it can print counters; absence means
    # no destruction event was observed, not a failure.  Any printed positive
    # value is still rejected.
    return all(int(values.get(k, "0")) == 0 for k in keys)


def all_one(values, keys):
    return all(int(values.get(k, "-999")) == 1 for k in keys)


def has_count(counts, key, value):
    return int(counts.get(key, "-1")) == value


def exact_assert(stderr):
    return ("Assertion failed: (!devs->num_hwctxs)" in stderr and
            "hwdec_devices_destroy" in stderr and
            re.search(r"file (?:video/)?hwdec\.c, line 31", stderr) is not None)


def barrier_line(stdout, stderr):
    combined = stdout + "\n" + stderr
    return "P28_TERMINAL" in combined and "op=barrier" in combined


def record(result, name, **kw):
    row = {"case": name, **kw}
    result["cases"].append(row)
    print(json.dumps({"case": name, "passed": row.get("passed"),
                      "exit": row.get("exitCode"),
                      "timedOut": row.get("timedOut")}, ensure_ascii=False))
    return row


def compile_harness(extracted, out, name, include_dir, extra=None):
    cmd = ["clang", "-std=c11", "-D_POSIX_C_SOURCE=200809L",
           "-DMP_OHCODEC_DIAGNOSTIC=1", "-Wall", "-Wextra",
           "-Wno-unused-function", "-Wno-unused-parameter",
           "-Wno-unused-variable", "-Wno-sign-compare",
           "-Wno-missing-field-initializers",
           "-Wno-default-const-init-field-unsafe",
           "-g", "-O0", "-fsanitize=address,undefined",
           "-fno-omit-frame-pointer", "-I", str(out),
           "-I", str(include_dir), str(HERE / "harness.c"),
           "-o", str(out / name), "-pthread"]
    if extra:
        cmd += extra
    c = subprocess.run(cmd, capture_output=True, text=True)
    (out / (name + ".compile.log")).write_text(c.stdout + c.stderr)
    return cmd, c.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mpv-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expect", choices=["red", "green"], required=True)
    args = ap.parse_args()
    out = args.out
    if out.exists():
        raise SystemExit("refusing to overwrite existing run root: %s" % out)
    out.mkdir(parents=True)
    extracted = out / "extracted"
    ex = subprocess.run([sys.executable, "-B", str(HERE / "extract.py"),
                         "--mpv-root", str(args.mpv_root),
                         "--out", str(extracted)], capture_output=True, text=True)
    (out / "extract.log").write_text(ex.stdout + ex.stderr)
    if ex.returncode:
        raise SystemExit("extract failed")

    binding = json.loads((extracted / "source-binding.json").read_text())
    result = {
        "phase": "Phase28 parent-release-chain",
        "mode": args.expect,
        "sourceRoot": str(args.mpv_root.resolve()),
        "sourceBinding": binding,
        "compile": {},
        "cases": [],
        "accepted": False,
        "formalArtifactAllowed": False,
    }
    cmd, rc = compile_harness(extracted, out, "harness", extracted)
    result["compile"] = {"command": cmd, "exit": rc}
    if rc:
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        raise SystemExit("compile failed; not accepted as RED")

    env = dict(os.environ, ASAN_OPTIONS="halt_on_error=1:detect_leaks=0",
               UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")

    if args.expect == "red":
        if binding.get("terminalBarrierPresent"):
            raise SystemExit("RED source unexpectedly contains terminal barrier")
        for case in ["preflight-unsafe", "late-unsafe"]:
            code, stdout, stderr, timed, alive = run_process(
                [str(out / "harness"), case], 15, env)
            (out / (case + ".log")).write_text(stdout + "\n--- stderr ---\n" + stderr)
            passed = (code == -6 and not timed and exact_assert(stderr)
                      and "EVENT destroy-queue" in stdout
                      and "EVENT uninit-begin" in stdout
                      and "EVENT video-chain-uninit" in stdout)
            record(result, case, exitCode=code, timedOut=timed,
                   exactAssert=exact_assert(stderr),
                   queueDestroyedBeforeExit="EVENT destroy-queue" in stdout,
                   realPlayerTailExercised=("EVENT video-chain-uninit" in stdout
                                            and "EVENT uninit-begin" in stdout),
                   passed=passed, stdout=stdout, stderr=stderr)
        for case in ["normal", "release-error", "normal-no-mapper"]:
            code, stdout, stderr, timed, alive = run_process(
                [str(out / "harness"), case], 15, env)
            (out / (case + ".log")).write_text(stdout + "\n--- stderr ---\n" + stderr)
            counts = parse_counts(stdout)
            parents = parse_parent_counts(stdout)
            passed = (code == 0 and not timed and not barrier_line(stdout, stderr)
                      and all_one(counts, CORE_DESTROY)
                      and all_one(parents, CRITICAL_PARENT)
                      and has_count(counts, "uninit_begin", 1)
                      and has_count(counts, "uninit_end", 1))
            if case != "normal-no-mapper":
                passed = passed and has_count(counts, "avctx_free", 1)
            record(result, case, exitCode=code, timedOut=timed,
                   counts=counts, parentCounts=parents,
                   passed=passed, stdout=stdout, stderr=stderr)
        result["accepted"] = all(c["passed"] for c in result["cases"])
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print("ACCEPTED" if result["accepted"] else "NOT ACCEPTED")
        raise SystemExit(0 if result["accepted"] else 1)

    # GREEN source: the barrier must exist and be bound into ohcodec_mapper_drain.
    if not binding.get("terminalBarrierPresent"):
        raise SystemExit("GREEN source lacks terminal barrier")

    for case in ["preflight-unsafe", "late-unsafe"]:
        code, stdout, stderr, timed, alive = run_process(
            [str(out / "harness"), case], 4.0, env)
        (out / (case + ".log")).write_text(stdout + "\n--- stderr ---\n" + stderr)
        counts = parse_counts(stdout)
        parents = parse_parent_counts(stdout)
        critical_zero = zero(parents, CRITICAL_PARENT)
        core_zero = zero(counts, CORE_DESTROY + ["uninit_end"])
        if case == "preflight-unsafe":
            early_zero = zero(counts, ["audio_out_free", "ipc_free",
                                       "video_chain_uninit", "uninit_begin"])
        else:
            early_zero = ("EVENT uninit-begin" in stdout and
                          int(counts.get("audio_out_free", "0")) <= 1 and
                          int(counts.get("ipc_free", "0")) <= 1 and
                          int(counts.get("video_chain_uninit", "0")) <= 1)
        bad = forbidden_events(stdout, case)
        passed = (timed and alive and barrier_line(stdout, stderr)
                  and not bad and critical_zero and core_zero and early_zero
                  and "Assertion failed" not in stderr
                  and "EVENT blocked-no-cleanup" in stdout)
        record(result, case, exitCode=code, timedOut=timed,
               aliveAtDeadline=alive, barrier=barrier_line(stdout, stderr),
               counts=counts, parentCounts=parents,
               forbiddenEvents=bad, criticalParentAbsent=critical_zero,
               coreDestroyAbsent=core_zero, earlyPathValid=early_zero,
               observerSnapshots=observer_destroy_events(stdout),
               passed=passed, stdout=stdout, stderr=stderr)

    # NativeImage callback dependency: the callback only touches the retained
    # surface lock/pending counter and must stay callable while the owner is
    # retained (its teardown is skipped/never reached on UNSAFE).
    code, stdout, stderr, timed, alive = run_process(
        [str(out / "harness"), "callback-retained"], 10, env)
    (out / "callback-retained.log").write_text(
        stdout + "\n--- stderr ---\n" + stderr)
    record(result, "callback-retained", exitCode=code, timedOut=timed,
           passed=(code == 0 and not timed and
                   "PASS callback-retained pending=2" in stdout),
           stdout=stdout, stderr=stderr)

    for case in ["normal", "release-error", "normal-no-mapper",
                 "late-normal", "late-release-error"]:
        code, stdout, stderr, timed, alive = run_process(
            [str(out / "harness"), case], 20, env)
        (out / (case + ".log")).write_text(stdout + "\n--- stderr ---\n" + stderr)
        counts = parse_counts(stdout)
        parents = parse_parent_counts(stdout)
        passed = (code == 0 and not timed and not barrier_line(stdout, stderr)
                  and all_one(counts, CORE_DESTROY)
                  and all_one(parents, CRITICAL_PARENT)
                  and has_count(counts, "uninit_begin", 1)
                  and has_count(counts, "uninit_end", 1))
        if case in ["normal", "release-error"]:
            passed = passed and has_count(counts, "avctx_free", 1)
        if case in ["release-error", "late-release-error"]:
            passed = passed and "Surface marked terminal" in stderr
        record(result, case, exitCode=code, timedOut=timed,
               counts=counts, parentCounts=parents,
               passed=passed, stdout=stdout, stderr=stderr)

    # Experiment build: the same barrier explicitly aborts.  A plain return,
    # SIGSEGV, or missing injection is not accepted.
    exp_out = out / "experiment"
    exp_out.mkdir()
    exp_extracted = exp_out / "extracted"
    shutil.copytree(extracted, exp_extracted)
    cmd, rc = compile_harness(exp_extracted, exp_out, "harness-experiment",
                              exp_extracted,
                              extra=["-DMP_OHCODEC_LIFECYCLE_EXPERIMENT=1"])
    if rc:
        record(result, "experiment", compileExit=rc, passed=False)
    else:
        code, stdout, stderr, timed, alive = run_process(
            [str(exp_out / "harness-experiment"), "experiment"], 15, env)
        (exp_out / "experiment.log").write_text(stdout + "\n--- stderr ---\n" + stderr)
        counts = parse_counts(stdout)
        parents = parse_parent_counts(stdout)
        critical_zero = zero(parents, CRITICAL_PARENT)
        core_zero = zero(counts, CORE_DESTROY + ["uninit_end"])
        bad = forbidden_events(stdout, "experiment")
        passed = (code == -6 and not timed and barrier_line(stdout, stderr)
                  and not bad and critical_zero and core_zero
                  and "Assertion failed" not in stderr)
        record(result, "experiment", exitCode=code, timedOut=timed,
               barrier=barrier_line(stdout, stderr),
               counts=counts, parentCounts=parents, forbiddenEvents=bad,
               criticalParentAbsent=critical_zero, coreDestroyAbsent=core_zero,
               passed=passed, stdout=stdout, stderr=stderr)

    # Negative control: remove both barrier calls (inner return only) and relax
    # the harness assertion implementation so the parent release becomes
    # observable instead of aborting.  This is a test-only probe, not product
    # behavior; the production source keeps the assertion.
    mut = out / "mutant"
    mut.mkdir()
    mut_ex = mut / "extracted"
    shutil.copytree(extracted, mut_ex)
    gen = mut_ex / "actual-generic.inc"
    original = gen.read_text()
    mutated = original.replace(
        'ohcodec_terminal_barrier(mapper->log, "drain-retained");',
        'return OHCODEC_DRAIN_UNSAFE;')
    mutated = mutated.replace(
        'ohcodec_terminal_barrier(mapper->log, "drain-unsafe");',
        'return OHCODEC_DRAIN_UNSAFE;')
    if mutated == original:
        record(result, "negative-inner-return-only",
               passed=False, error="could not remove barrier call")
    else:
        gen.write_text(mutated)
        (mut / "mutation.json").write_text(json.dumps({
            "file": "actual-generic.inc",
            "before": original,
            "after": mutated,
            "rule": "replace barrier call with return OHCODEC_DRAIN_UNSAFE",
            "purpose": "negative control only; production source retains assert",
        }, indent=2) + "\n")
        cmd, rc = compile_harness(mut_ex, mut, "harness-mutant", mut_ex)
        if rc:
            record(result, "negative-inner-return-only",
                   compileExit=rc, passed=False)
        else:
            code, stdout, stderr, timed, alive = run_process(
                [str(mut / "harness-mutant"), "relaxed-mutant"], 15, env)
            (mut / "relaxed.log").write_text(stdout + "\n--- stderr ---\n" + stderr)
            counts = parse_counts(stdout)
            parents = parse_parent_counts(stdout)
            passed = (code == 0 and not timed
                      and "ASSERT_RELAXED" in stderr
                      and all_one(counts, CORE_DESTROY)
                      and all_one(parents, CRITICAL_PARENT))
            record(result, "negative-inner-return-only",
                   exitCode=code, timedOut=timed, counts=counts,
                   parentCounts=parents, parentReleased=True, passed=passed,
                   stdout=stdout, stderr=stderr)

    # Negative control for R1: mutate the real vo_thread tail (not a hand
    # model) to destroy the hwdec registry immediately before driver uninit.
    # The late-unsafe test must reject it with the exact registry assertion; if
    # vo_thread were not compiled into the harness this would only time out.
    tail = out / "vo-tail-mutant"
    tail.mkdir()
    tail_ex = tail / "extracted"
    shutil.copytree(extracted, tail_ex)
    vt = tail_ex / "actual-vo.inc"
    vorig = vt.read_text()
    vmut = vorig.replace(
        "    vo->driver->uninit(vo);",
        "    hwdec_devices_destroy(vo->hwdec_devs);\n"
        "    vo->driver->uninit(vo);")
    if vmut == vorig:
        record(result, "negative-real-vo-tail-early-destroy",
               passed=False, error="could not mutate real vo_thread tail")
    else:
        vt.write_text(vmut)
        (tail / "mutation.json").write_text(json.dumps({
            "file": "actual-vo.inc",
            "rule": "insert hwdec_devices_destroy(vo->hwdec_devs) before "
                    "vo->driver->uninit(vo) in the real vo_thread",
            "sourceSHA256Before": hashlib.sha256(vorig.encode()).hexdigest(),
            "sourceSHA256After": hashlib.sha256(vmut.encode()).hexdigest(),
            "purpose": "R1 negative control; production source unchanged",
        }, indent=2) + "\n")
        cmd, rc = compile_harness(tail_ex, tail, "harness-vo-tail", tail_ex)
        if rc:
            record(result, "negative-real-vo-tail-early-destroy",
                   compileExit=rc, passed=False)
        else:
            code, stdout, stderr, timed, alive = run_process(
                [str(tail / "harness-vo-tail"), "late-unsafe"], 8, env)
            (tail / "late-unsafe.log").write_text(
                stdout + "\n--- stderr ---\n" + stderr)
            passed = (not timed and code == -6 and exact_assert(stderr))
            record(result, "negative-real-vo-tail-early-destroy",
                   exitCode=code, timedOut=timed,
                   exactAssert=exact_assert(stderr),
                   realVoTailExercised=exact_assert(stderr),
                   passed=passed, stdout=stdout, stderr=stderr)

    # F1 negative: move the existing pl_queue_destroy before the late drain.
    # The event must be visible immediately; the gate must reject the mutant
    # instead of treating missing final counts as zero.
    qtail = out / "queue-before-drain-mutant"
    qtail.mkdir()
    qtail_ex = qtail / "extracted"
    shutil.copytree(extracted, qtail_ex)
    qf = qtail_ex / "actual-vo_gpu_next.inc"
    qorig = qf.read_text()
    qline = "    pl_queue_destroy(&p->queue); // destroy this first\n"
    qmut = qorig.replace(qline, "", 1)
    qmut = qmut.replace("    struct priv *p = vo->priv;\n",
                        "    struct priv *p = vo->priv;\n" + qline, 1)
    if qmut == qorig:
        record(result, "negative-queue-destroy-before-drain",
               passed=False, error="could not move queue destroy")
    else:
        qf.write_text(qmut)
        (qtail / "mutation.json").write_text(json.dumps({
            "file": "actual-vo_gpu_next.inc",
            "rule": "move existing pl_queue_destroy before the late drain",
            "beforeSHA256": hashlib.sha256(qorig.encode()).hexdigest(),
            "afterSHA256": hashlib.sha256(qmut.encode()).hexdigest(),
            "purpose": "F1 negative control; production source unchanged",
        }, indent=2) + "\n")
        cmd, rc = compile_harness(qtail_ex, qtail, "harness-queue-move", qtail_ex)
        if rc:
            record(result, "negative-queue-destroy-before-drain",
                   compileExit=rc, passed=False)
        else:
            code, stdout, stderr, timed, alive = run_process(
                [str(qtail / "harness-queue-move"), "late-unsafe"], 5, env)
            (qtail / "late-unsafe.log").write_text(
                stdout + "\n--- stderr ---\n" + stderr)
            events = destroy_events(stdout)
            passed = (timed and "EVENT destroy-queue" in stdout and
                      "P28_TERMINAL" in stdout + stderr)
            record(result, "negative-queue-destroy-before-drain",
                   exitCode=code, timedOut=timed, events=events,
                   latePath="EVENT uninit-begin" in stdout,
                   passed=passed, stdout=stdout, stderr=stderr)

    result["accepted"] = all(c.get("passed") for c in result["cases"])
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print("ACCEPTED" if result["accepted"] else "NOT ACCEPTED")
    raise SystemExit(0 if result["accepted"] else 1)


if __name__ == "__main__":
    main()
