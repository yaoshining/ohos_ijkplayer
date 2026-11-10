/* Diagnostic build only. Include after Phase30's ref and trace declarations. */
#include <hilog/log.h>

static atomic_bool probe_injected;

static OH_AVErrCode probe_close_call(OHCodecDecRef *ref, bool destroy)
{
    bool inject = destroy == PROBE_DESTROY && ref->start_attempted &&
                  ref->window && !atomic_exchange(&probe_injected, true);
    OH_AVErrCode rc;
    if (inject)
        rc = AV_ERR_UNKNOWN;
    else
        rc = destroy ? OH_VideoDecoder_Destroy(ref->dec) : OH_VideoDecoder_Stop(ref->dec);
    OH_LOG_Print(LOG_APP, LOG_INFO, 0xD001, "CloseVerify",
                 "op=%{public}s skipped=%{public}d rc=%{public}d decoder=%{public}llu surface=%{public}llu",
                 destroy ? "destroy" : "stop", inject, rc,
                 (unsigned long long)ref->trace_instance, (unsigned long long)ref->surface_id);
    return rc;
}
