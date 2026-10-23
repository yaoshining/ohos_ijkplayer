/* Diagnostic-only consumer identity/admission. Never exports an ABI. */
#include <pthread.h>
#include <native_window/external_window.h>
static atomic_uint_fast64_t ohcodec_diagnostic_serial;
static pthread_mutex_t ohcodec_diagnostic_mutex = PTHREAD_MUTEX_INITIALIZER;
static struct { uint64_t surface, instance; } ohcodec_diagnostic_consumers[16];

static void ohcodec_diagnostic_log(AVCodecContext *avctx, OHCodecDecRef *ref,
                                   const char *op, int rc)
{
    av_log(avctx, AV_LOG_INFO,
           "P28D_CODEC t=%"PRId64" op=%s instance=%"PRIu64" gen=%"PRIu64
           " consumer=%"PRIu64" claimed=%d rc=%d\n",
           p27_monotonic_us(), op, ref->diagnostic_instance,
           (uint64_t)atomic_load(&ref->generation), ref->diagnostic_surface,
           ref->diagnostic_claimed, rc);
}

static bool ohcodec_diagnostic_claim(OHCodecDecRef *ref, uint64_t surface)
{
    if (ref->diagnostic_claimed && ref->diagnostic_surface != surface) return false;
    bool admitted = false;
    int empty = -1;
    pthread_mutex_lock(&ohcodec_diagnostic_mutex);
    for (int i = 0; i < 16; i++) {
        if (ohcodec_diagnostic_consumers[i].surface == surface) {
            admitted = ohcodec_diagnostic_consumers[i].instance == ref->diagnostic_instance;
            goto done;
        }
        if (!ohcodec_diagnostic_consumers[i].surface && empty < 0) empty = i;
    }
    if (empty >= 0) {
        ohcodec_diagnostic_consumers[empty].surface = surface;
        ohcodec_diagnostic_consumers[empty].instance = ref->diagnostic_instance;
        admitted = true;
    }
done:
    if (admitted) {
        ref->diagnostic_surface = surface;
        ref->diagnostic_claimed = true;
    }
    pthread_mutex_unlock(&ohcodec_diagnostic_mutex);
    return admitted;
}

static void ohcodec_diagnostic_release(OHCodecDecRef *ref)
{
    pthread_mutex_lock(&ohcodec_diagnostic_mutex);
    for (int i = 0; i < 16; i++) {
        if (ohcodec_diagnostic_consumers[i].surface == ref->diagnostic_surface &&
            ohcodec_diagnostic_consumers[i].instance == ref->diagnostic_instance) {
            ohcodec_diagnostic_consumers[i].surface = 0;
            ohcodec_diagnostic_consumers[i].instance = 0;
        }
    }
    ref->diagnostic_claimed = false;
    pthread_mutex_unlock(&ohcodec_diagnostic_mutex);
}

/* Controlled interleaving probe: a second registry identity only. No second
 * platform decoder or SetSurface call is made by this diagnostic probe. */
static bool ohcodec_diagnostic_challenge(AVCodecContext *avctx, OHCodecDecRef *ref)
{
    OHCodecDecRef second = {0};
    second.diagnostic_instance = atomic_fetch_add(&ohcodec_diagnostic_serial, 1) + 1;
    bool admitted = ohcodec_diagnostic_claim(&second, ref->diagnostic_surface);
    av_log(avctx, AV_LOG_INFO,
           "P28D_CODEC t=%"PRId64" op=admission-challenge kind=registry-only "
           "held_instance=%"PRIu64" requested_instance=%"PRIu64" consumer=%"PRIu64
           " platform_called=0 rejected=%d\n",
           p27_monotonic_us(), ref->diagnostic_instance, second.diagnostic_instance,
           ref->diagnostic_surface, !admitted);
    if (admitted) ohcodec_diagnostic_release(&second);
    return !admitted;
}
