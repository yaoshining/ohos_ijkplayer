"""Strict cleanup evidence gate for the diagnostic device runs.

An empty stdout is not proof of absence.  Every "absent" claim must come from a
successful query with a recognizable response, the target must be explicitly
Connected, and the force-stop must be acknowledged.  Timeouts, transport
errors, Offline targets and missing records are unknown/failed.
"""
import re

TARGET = "192.168.3.85:5555"
BUNDLE = "com.yaoshining.phase22probe"
ERROR_MARKERS = ["[Fail]", "error:", "No such file", "Permission denied",
                 "Error Code:", "timed out", "timeout", "not found"]


def tail(cmd):
    for i, x in enumerate(cmd):
        if x in ("shell", "list"):
            return cmd[i:]
    return cmd


def no_error_text(text):
    low = text.lower()
    return not any(m.lower() in low for m in ERROR_MARKERS)


def valid_command(d, allowed_exit=(0,)):
    if not d or d.get("timeout") is not None:
        return False
    if d.get("exit") not in allowed_exit:
        return False
    return no_error_text(d.get("stdout", "") + d.get("stderr", ""))


def valid_pid_absent(d):
    # pidof commonly returns 0 with empty output; some builds return 1.
    return (valid_command(d, allowed_exit=(0, 1)) and
            not d.get("stdout", "").strip())


def find_start(commands):
    for i, c in enumerate(commands):
        t = tail(c.get("command", []))
        if len(t) >= 4 and t[:3] == ["shell", "aa", "start"] and BUNDLE in t:
            return i
    return None


def after(commands, idx, start_idx, predicate):
    for c in commands[idx + 1:]:
        t = tail(c.get("command", []))
        if predicate(t):
            return c
    return None


def target_connected(d):
    if not valid_command(d):
        return False
    for line in d.get("stdout", "").splitlines():
        if re.match(r"^\s*" + re.escape(TARGET) + r"\s+TCP\s+Connected(?:\s|$)",
                    line):
            return True
    return False


def target_offline(d):
    if not d:
        return False
    for line in d.get("stdout", "").splitlines():
        if TARGET in line and re.search(r"\bOffline\b", line):
            return True
    return False


def derive_cleanup(commands, bundle=BUNDLE):
    start = find_start(commands)
    checks = {
        "startCommandPresent": start is not None,
        "stopCommandSucceeded": False,
        "pidQueryValid": False,
        "pidAbsent": False,
        "targetConnected": False,
        "targetOffline": False,
        "abilityQueryValid": False,
        "abilityAbsent": False,
        "windowQueryValid": False,
        "windowAbsent": False,
        "cleanupEvidenceValid": False,
    }
    detail = {}
    if start is None:
        detail["error"] = "no successful aa start record"
        return checks, detail
    stop_idx = None
    for i in range(start + 1, len(commands)):
        t = tail(commands[i].get("command", []))
        if (len(t) >= 4 and t[:3] == ["shell", "aa", "force-stop"] and
                bundle in t):
            stop_idx = i
    if stop_idx is None:
        detail["error"] = "no force-stop record after start"
        return checks, detail
    stop = commands[stop_idx]
    detail["stop"] = stop
    checks["stopCommandSucceeded"] = (
        valid_command(stop) and
        "force stop process successfully" in stop.get("stdout", ""))
    pid = after(commands, stop_idx, start,
                lambda t: len(t) >= 3 and t[:2] == ["shell", "pidof"] and
                bundle in t)
    detail["pidAfter"] = pid
    checks["pidQueryValid"] = bool(pid) and valid_pid_absent(pid)
    checks["pidAbsent"] = checks["pidQueryValid"]
    windows = after(commands, stop_idx, start,
                    lambda t: "WindowManagerService" in t)
    detail["windowsAfter"] = windows
    checks["windowQueryValid"] = bool(
        windows and valid_command(windows) and
        "WindowManagerService" in windows.get("stdout", "") and
        "Total window num" in windows.get("stdout", ""))
    checks["windowAbsent"] = (
        checks["windowQueryValid"] and
        "phase22probe" not in windows.get("stdout", ""))
    abilities = after(commands, stop_idx, start,
                      lambda t: len(t) >= 3 and t[:3] == ["shell", "aa", "dump"])
    detail["abilitiesAfter"] = abilities
    checks["abilityQueryValid"] = bool(
        abilities and valid_command(abilities) and
        any(x in abilities.get("stdout", "") for x in
            ["AbilityManagerService", "current mission lists", "AbilityRecord"]))
    checks["abilityAbsent"] = (
        checks["abilityQueryValid"] and
        bundle not in abilities.get("stdout", ""))
    targets = after(commands, stop_idx, start,
                    lambda t: len(t) >= 3 and t[:2] == ["list", "targets"])
    detail["targets"] = targets
    checks["targetConnected"] = bool(targets and target_connected(targets))
    checks["targetOffline"] = bool(targets and target_offline(targets))
    checks["cleanupEvidenceValid"] = all(checks[k] for k in
        ["stopCommandSucceeded", "pidQueryValid", "targetConnected",
         "abilityQueryValid", "windowQueryValid"])
    return checks, detail
