/*
 * T005 real-function harness: mapper/VO/vd_lavc lifecycle ordering.
 *
 * Actual production function bodies are included from actual-*.inc, extracted
 * verbatim by extract.py. Only external dependencies (Vulkan, libplacebo,
 * HarmonyOS platform, talloc, FFmpeg, mpv dispatch) are stubbed. Event order is
 * recorded with a monotonic sequence number.
 */
#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define AVERROR_EOF (-541478725)
#define AVERROR_BUG (-100)
#define AVERROR(e) (-(e))
#include <errno.h>
#include <unistd.h>

/* ---------------------------------------------------------------- events */
enum {
    EV_HOLD = 1, EV_SIGNAL, EV_WAIT, EV_RELEASE, EV_FINISH, EV_FINAL,
    EV_DESTROY, EV_PREFLIGHT, EV_FLUSH, EV_FREE, EV_DRIVER, EV_RETIRE,
};
static const char *ev_name(int e) {
    switch (e) {
    case EV_HOLD: return "hold";
    case EV_SIGNAL: return "signal_release";
    case EV_WAIT: return "queue_wait_idle";
    case EV_RELEASE: return "release_window_buffer";
    case EV_FINISH: return "gpu_finish";
    case EV_FINAL: return "last_ref_finalized";
    case EV_DESTROY: return "import_destroyed";
    case EV_PREFLIGHT: return "preflight_drain";
    case EV_FLUSH: return "ffmpeg_flush";
    case EV_FREE: return "ffmpeg_free";
    case EV_DRIVER: return "vo_driver_control";
    case EV_RETIRE: return "vo_retire_frames";
    default: return "?";
    }
}
static int events[256], nevents;
static void ev(int e) { if (nevents < (int)(sizeof(events)/sizeof(events[0]))) events[nevents++] = e; }
static int first_ev(int e) { for (int i = 0; i < nevents; i++) if (events[i] == e) return i; return -1; }
static void dump_events(void) {
    for (int i = 0; i < nevents; i++) printf("%s%s", i ? "," : "", ev_name(events[i]));
    printf("\n");
}

/* ------------------------------------------------------------- base types */
typedef struct { int unused; } OHNativeWindow;
typedef struct { int unused; } OHNativeWindowBuffer;
typedef struct { int unused; } OH_NativeBuffer;
typedef struct { int unused; } OH_AVCodec;
typedef struct { int unused; } OH_AVFormat;
typedef struct { int unused; } AVOHCodecBuffer;
typedef void *pl_gpu;
typedef uint64_t VkSemaphore;
typedef uint64_t VkImage;
typedef int VkResult;
typedef void *pl_tex;
typedef struct { int layout; } pl_tex_layout;
#define VK_SUCCESS 0
#define VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL 5
#define VK_QUEUE_FAMILY_EXTERNAL 0xffffffffu
#define NATIVE_ERROR_OK 0
#define NATIVE_ERROR_NO_BUFFER (-1)
#define OHCODEC_DRAIN_NOT_APPLICABLE 0
#define OHCODEC_DRAIN_SAFE 1
#define OHCODEC_DRAIN_SAFE_RELEASE_ERROR 2
#define OHCODEC_DRAIN_UNSAFE 3
#define OHCODEC_DRAIN_REASON_CLOSE 2
#define VO_OHCODEC_DRAIN_REASON_SEEK 1
#define VO_OHCODEC_DRAIN_REASON_CLOSE 2
#define VO_OHCODEC_DRAIN_REASON_REINIT 3
#define VO_OHCODEC_DRAIN_REASON_RESUME 4
#define VO_MAX_REQ_FRAMES 3

struct mp_image { int id; int imgfmt; void *planes[4]; int64_t pts, dts, pkt_duration; };
static void mp_image_unrefp(struct mp_image **p) {
    if (*p) { ev(EV_FINAL); free(*p); *p = NULL; }
}
static void *talloc_free(void *p) { free(p); return NULL; }
static int64_t mp_time_ns(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return (int64_t)ts.tv_sec*1000000000+ts.tv_nsec; }
#define MP_INFO(...) ((void)0)
#define MP_ERR(...) ((void)0)
#define MP_TRACE(...) ((void)0)
#define MP_VERBOSE(...) ((void)0)

/* mpv mutex/talloc shims used by the VO slice */
typedef struct { int locked; } mp_mutex;
typedef struct { int unused; } mp_cond;
static int mp_mutex_init(mp_mutex *m) { m->locked = 0; return 0; }
static void mp_mutex_destroy(mp_mutex *m) { (void)m; }
static void mp_mutex_lock(mp_mutex *m) { m->locked++; }
static void mp_mutex_unlock(mp_mutex *m) { m->locked--; }
static int mp_cond_init(mp_cond *c) { (void)c; return 0; }
static void mp_cond_destroy(mp_cond *c) { (void)c; }
static void mp_cond_signal(mp_cond *c) { (void)c; }

/* --------------------------------------------------------- generic hwdec */
struct ra_tex;
struct ra_hwdec;
struct ra_hwdec_mapper;
struct ohcodec_interop {
    void (*owner_uninit)(struct ra_hwdec *);
    bool (*mapper_init)(struct ra_hwdec_mapper *);
    void (*mapper_uninit)(struct ra_hwdec_mapper *);
    int (*map)(struct ra_hwdec_mapper *);
    int (*reuse)(struct ra_hwdec_mapper *);
    void (*unmap)(struct ra_hwdec_mapper *);
    void (*release)(struct ra_hwdec_mapper *);
    /* Phase28 addition; absent in baseline. */
    int (*drain)(struct ra_hwdec_mapper *, int reason, int *platform_error);
};
struct ohcodec_surface { void *image; void *window; };
struct ohcodec_priv {
    struct ohcodec_interop *interop;
    void *interop_owner_priv;
    struct ohcodec_surface *surface;
    bool surface_invalid;
};
struct ohcodec_mapper_priv {
    void *priv;
    AVOHCodecBuffer *last_token;
    struct mp_image *last_src;
};
struct ra_hwdec { const struct ra_hwdec_driver *driver; void *priv; struct mp_log *log; bool resource_retained; };
struct ra { int unused; };
struct ra_hwdec_mapper {
    const struct ra_hwdec_mapper_driver *driver;
    struct mp_log *log;
    struct ra *ra;
    void *priv;
    struct ra_hwdec *owner;
    bool resource_retained;
    struct mp_image *src;
    struct ra_tex *tex[4];
    int src_params_placeholder;
};
struct ra_hwdec_mapper_driver { size_t priv_size; int (*init)(struct ra_hwdec_mapper *); void (*uninit)(struct ra_hwdec_mapper *); int (*map)(struct ra_hwdec_mapper *); void (*unmap)(struct ra_hwdec_mapper *); };
struct ra_hwdec_driver { const char *name; int device_type; void (*uninit)(struct ra_hwdec *); };
#define AV_HWDEVICE_TYPE_OHCODEC 100

/* ---------------------------------------------------- Vulkan/libplacebo */
struct vk_import {
    struct vk_import *next;
    uint32_t seq;
    void *native_buffer;
    VkImage image;
    VkSemaphore acquire_sem;
    VkSemaphore release_sem;
    pl_tex pltex;
    void *ratex;
    bool busy;
};
struct pl_vulkan {
    void *device;
    void (*lock_queue)(struct pl_vulkan *, uint32_t qf, uint32_t index);
    void (*unlock_queue)(struct pl_vulkan *, uint32_t qf, uint32_t index);
};
struct vk_mapper {
    pl_gpu gpu;
    struct pl_vulkan *vk;
    void *get_props;
    void *acquire_image;
    int (*signal_release)(void *queue, uint32_t n, VkSemaphore *sem, VkImage image, int *fence_fd);
    int (*wait_idle)(void *queue);
    void *queue;
    uint32_t qf;
    void *rgba8;
    void *rgba16;
    struct vk_import *imports;
    int num_imports;
    struct vk_import *current;
    OHNativeWindowBuffer *window_buffer;
    const char *release_reason;
    bool external_release_inflight;
};
struct pl_vulkan_hold_params {
    void *tex;
    int layout;
    uint32_t qf;
    struct { VkSemaphore sem; } semaphore;
};
#define pl_vulkan_hold_params(...) ((struct pl_vulkan_hold_params){ __VA_ARGS__ })
static bool hold_result = true;
static bool pl_vulkan_hold_ex(pl_gpu gpu, struct pl_vulkan_hold_params p) {
    (void)gpu; (void)p;
    if (!hold_result) return false;
    ev(EV_HOLD);
    return true;
}
static void pl_gpu_finish(pl_gpu gpu) { (void)gpu; ev(EV_FINISH); }
static void fake_lock_queue(struct pl_vulkan *vk, uint32_t qf, uint32_t i) { (void)vk; (void)qf; (void)i; }
static void fake_unlock_queue(struct pl_vulkan *vk, uint32_t qf, uint32_t i) { (void)vk; (void)qf; (void)i; }
static int release_result = NATIVE_ERROR_OK;
static int signal_result = VK_SUCCESS;
static int queue_wait_result = VK_SUCCESS;
static int fake_signal_release(void *queue, uint32_t n, VkSemaphore *sem, VkImage image, int *fence_fd) {
    (void)queue; (void)n; (void)sem; (void)image;
    ev(EV_SIGNAL);
    if (signal_result == VK_SUCCESS) *fence_fd = 42;
    return signal_result;
}
static int wait_calls;
static VkResult fake_queue_wait_idle(void *queue) { (void)queue; ev(EV_WAIT); wait_calls++; return queue_wait_result; }
static int OH_NativeBuffer_FromNativeWindowBuffer(OHNativeWindowBuffer *b, OH_NativeBuffer **n) { (void)b; *n = (OH_NativeBuffer *)b; return NATIVE_ERROR_OK; }
static uint32_t OH_NativeBuffer_GetSeqNum(OH_NativeBuffer *n) { return (uint32_t)(uintptr_t)n; }
static int OH_NativeImage_ReleaseNativeWindowBuffer(void *image, OHNativeWindowBuffer *b, int fence) {
    (void)image; (void)b; (void)fence; ev(EV_RELEASE); return release_result;
}
static void OH_NativeWindow_NativeObjectUnreference(OHNativeWindowBuffer *b) { (void)b; }

/* bridge talloc allocate for vk_import */
static void *vk_alloc(void) { return calloc(1, sizeof(struct vk_import)); }

/* Stub for the backend import destructor. The ordering under test is the
 * release/final-ref/GPU-finish sequence, not import memory management. */
static void destroy_import(struct ra_hwdec_mapper *mapper, struct vk_import *e) {
    (void)mapper; ev(EV_DESTROY); free(e);
}


/* --------------------------------------------------------- vd_lavc stubs */
struct mp_log { int unused; };
struct mp_filter { void *priv; struct mp_log *log; void *packet_pool; };
struct hwdec_info { char name[64]; char method_name[24]; int lavc_device; int pix_fmt; bool use_hw_frames; };
struct hwdec_opts { int software_fallback; };
struct mp_hwdec_devices;
struct mp_image_pool;
struct mp_codec_params;
struct vd_lavc_params;
struct hwdec_opts;
struct m_config_cache;
struct demux_packet;
struct mp_decoder;
enum AVDiscard { AVDISCARD_NONE = 0, AVDISCARD_ALL = 3 };
typedef struct AVPacket { int size; } AVPacket;
typedef struct AVRational { int num, den; } AVRational;
typedef struct AVBufferRef AVBufferRef;
typedef struct AVFrame { int unused; AVBufferRef *buf[8]; int64_t pts, pkt_dts, duration; } AVFrame;
typedef struct AVBufferRef { int unused; } AVBufferRef;
typedef struct AVCodecContext { int codec_id; int width, height; void *priv_data; enum AVDiscard skip_frame; } AVCodecContext;
typedef struct vd_ffmpeg_ctx vd_ffmpeg_ctx;
struct vd_ffmpeg_ctx {
    struct mp_log *log;
    AVCodecContext *avctx;
    AVFrame *pic;
    AVPacket *avpkt;
    bool use_hwdec;
    struct hwdec_info hwdec;
    bool flushing;
    bool eof_deferred;              /* Phase28 addition */
    bool lifecycle_unsafe;          /* Phase28 addition */
    bool lifecycle_release_error;   /* Phase28 addition */
    bool lifecycle_failed;          /* Phase28 addition */
    struct vo *vo;
    struct mp_hwdec_devices *hwdec_devs;
    AVBufferRef *hwdec_dev;
    bool hwdec_request_reinit;
    bool hwdec_failed;
    bool hwdec_notified;
    bool hwdec_deferred_for_eof;    /* possible naming in implementation */
    int num_delay_queue;
    struct mp_image **delay_queue;
    int num_sent_packets;
    struct demux_packet **sent_packets;
    int num_requeue_packets;
    struct demux_packet **requeue_packets;
    int hwdec_fail_count;
    bool hw_probing;
    struct mp_codec_params *codec;
    AVRational codec_timebase;
    struct hwdec_opts *hwdec_opts;
    bool force_eof;
    int max_delay_queue;
    AVBufferRef *cached_hw_frames_ctx;
    struct hwdec_info hwdec_unused;
};
static int avcodec_is_open(AVCodecContext *avctx) { return avctx != NULL; }
static void avcodec_flush_buffers(AVCodecContext *avctx) { (void)avctx; ev(EV_FLUSH); }
static void av_frame_free(AVFrame **f) { free(*f); *f = NULL; }
static void mp_free_av_packet(AVPacket **p) { free(*p); *p = NULL; }
static void av_buffer_unref(AVBufferRef **r) { free(*r); *r = NULL; }
static void avcodec_free_context(AVCodecContext **a) { ev(EV_FREE); free(*a); *a = NULL; }

/* The preflight result ABI shared between vd_lavc, vo.c and vo_gpu_next. */
enum {
    VO_OHCODEC_DRAIN_NOT_APPLICABLE = 0,
    VO_OHCODEC_DRAIN_SAFE = 1,
    VO_OHCODEC_DRAIN_SAFE_RELEASE_ERROR = 2,
    VO_OHCODEC_DRAIN_UNSAFE = 3,
};
struct vo_ohcodec_drain_req { int result; int platform_error; int reason; };
struct vo_ohcodec_surface_req { int invalid; int mark_invalid; };
#define VOCTRL_OHCODEC_DRAIN 0x4f484344 /* 'OHCD' */
#define VOCTRL_OHCODEC_SURFACE 0x4f484353 /* 'OHCS' */

/* --------------------------------------------------------------- VO stubs */
void vo_ohcodec_retire_frames(struct vo *vo);
struct vo_frame { int id; };
typedef struct mp_dispatch_queue { int unused; } mp_dispatch_queue;
struct vo_internal {
    mp_mutex lock;
    bool hasframe;
    bool hasframe_rendered;
    bool send_reset;
    bool request_redraw;
    bool want_redraw;
    struct vo_frame *current_frame;
    struct vo_frame *frame_queued;
    uint64_t current_frame_id;
    mp_dispatch_queue *dispatch;
    mp_cond wakeup;
    bool paused;
};
struct vo_driver { int (*control)(struct vo *, uint32_t, void *); const char *name; };
struct vo { struct vo_internal *in; const struct vo_driver *driver; bool want_redraw; };
static int driver_saw_current;
static int driver_saw_queued;
static struct vo_ohcodec_drain_req *driver_req;
static int driver_result = VO_OHCODEC_DRAIN_SAFE;
static int surface_invalid, surface_marks, surface_queries;
static int fake_driver_control(struct vo *vo, uint32_t request, void *data) {
    (void)vo;
    ev(EV_DRIVER);
    if (request == VOCTRL_OHCODEC_SURFACE && data) {
        struct vo_ohcodec_surface_req *req = data;
        surface_queries++;
        if (req->mark_invalid) {
            surface_marks++;
            surface_invalid = 1;
        }
        req->invalid = surface_invalid;
        return 0;
    }
    if (request == VOCTRL_OHCODEC_DRAIN && data) {
        ev(EV_PREFLIGHT);
#ifdef PHASE28
        if (driver_result != VO_OHCODEC_DRAIN_NOT_APPLICABLE)
            vo_ohcodec_retire_frames(vo);
#endif
        driver_saw_current = vo->in->current_frame != NULL;
        driver_saw_queued = vo->in->frame_queued != NULL;
        driver_req = data;
        driver_req->result = driver_result ? driver_result : VO_OHCODEC_DRAIN_SAFE;
        return 0;
    }
    return -1;
}
static void update_opts(struct vo *vo) { (void)vo; }
static void mp_dispatch_run(mp_dispatch_queue *q, void (*fn)(void *), void *p) { (void)q; fn(p); }

/* --------------------------------------------------- decode/EOF stubs */
struct demux_packet { int size; };
enum { IMGFMT_CUDA = 999 };
static int avcodec_receive_frame(AVCodecContext *a, AVFrame *f) { (void)a; (void)f; return AVERROR_EOF; }
static int avcodec_send_packet(AVCodecContext *a, const AVPacket *p) { (void)a; (void)p; return 0; }
static void av_frame_unref(AVFrame *f) { (void)f; }
static void prepare_decoding(struct mp_filter *vd) { (void)vd; }
static void send_queued_packet(struct mp_filter *vd) { (void)vd; }
static void handle_err(struct mp_filter *vd) { (void)vd; }
static void mp_codec_info_from_av(AVCodecContext *a, void *c) { (void)a; (void)c; }
static struct mp_image *mp_image_from_av_frame(AVFrame *f) { (void)f; return NULL; }
static int64_t mp_pts_from_av(int64_t pts, AVRational *tb) { (void)tb; return pts; }
static void mp_set_av_packet(AVPacket *dst, struct demux_packet *src, AVRational *tb) { (void)dst; (void)src; (void)tb; }
static struct demux_packet *demux_copy_packet(void *pool, struct demux_packet *p) { (void)pool; return p; }
#define mp_assert(x) do { if (!(x)) abort(); } while (0)
#define MP_TARRAY_APPEND(ctx, arr, num, item) do { (void)(ctx); (void)(arr); (void)(num); (void)(item); } while (0)

static void reset_vsync_timings(struct vo *vo) { (void)vo; }
static void wakeup_locked(struct vo *vo) { (void)vo; }
static void forget_frames(struct vo *vo) {
    struct vo_internal *in = vo->in;
    talloc_free(in->frame_queued);
    in->frame_queued = NULL;
    in->hasframe = false;
    in->hasframe_rendered = false;
}

/* Forward declarations required by the verbatim slices. */
int vo_control(struct vo *vo, int request, void *data);
static void mapper_release(struct ra_hwdec_mapper *mapper);
void ohcodec_mapper_mark_surface_invalid(struct ra_hwdec_mapper *mapper);
bool ohcodec_hwdec_surface_invalid(struct ra_hwdec *hw);
void ohcodec_hwdec_mark_surface_invalid(struct ra_hwdec *hw);
struct ra_hwdec *ohcodec_hwdec_find(struct ra_hwdec **hwdecs, int num);
void ra_hwdec_mapper_unmap(struct ra_hwdec_mapper *mapper);
static bool fake_mapper_init(struct ra_hwdec_mapper *mapper) { (void)mapper; return true; }
static void uninit_avctx(struct mp_filter *vd);
static void reset_vsync_timings(struct vo *vo);
static void wakeup_locked(struct vo *vo);
static void forget_frames(struct vo *vo);

/* Actual production functions (verbatim slices). */
#define mapper_uninit vk_mapper_uninit
#include "actual-vk.inc"
#undef mapper_uninit
#include "actual-generic.inc"
#include "actual-gpu.inc"
#include "actual-vd.inc"
#include "actual-vo.inc"

/* ------------------------------------------------------------ test modes */
static struct vk_mapper *make_vk(struct ra_hwdec_mapper *mapper, struct ohcodec_mapper_priv *mp) {
    struct vk_mapper *v = calloc(1, sizeof(*v));
    struct pl_vulkan *vk = calloc(1, sizeof(*vk));
    struct vk_import *e = vk_alloc();
    vk->lock_queue = fake_lock_queue;
    vk->unlock_queue = fake_unlock_queue;
    v->vk = vk;
    v->gpu = (pl_gpu)1;
    v->signal_release = fake_signal_release;
    v->wait_idle = fake_queue_wait_idle;
    v->qf = 0;
    v->current = e;
    v->imports = NULL;
    v->num_imports = 1;
    v->window_buffer = (OHNativeWindowBuffer *)(uintptr_t)0x100;
    e->busy = true;
    e->seq = 7;
    mp->priv = v;
    mapper->priv = mp;
    return v;
}

static int mode_mapper_uninit(void) {
    struct ra_hwdec_mapper mapper = {0};
    struct ohcodec_priv owner = {0};
    struct ohcodec_mapper_priv mp = {0};
    struct mp_image *img = calloc(1, sizeof(*img));
    struct ohcodec_interop interop = {0};
    struct ohcodec_surface surface = { .image = (void *)(uintptr_t)0x55 };
    struct ra_hwdec hw = {0};
    hw.priv = &owner;
    owner.interop = &interop;
    owner.surface = &surface;
    mapper.owner = &hw;
    mapper.priv = &mp;
    mp.last_token = (AVOHCodecBuffer *)(uintptr_t)0x200;
    mp.last_src = img;
    make_vk(&mapper, &mp);
    interop.release = mapper_release;
    interop.mapper_uninit = vk_mapper_uninit;
#ifdef PHASE28
    interop.drain = ohcodec_drain;
#endif

    mapper_uninit(&mapper);
    dump_events();
    int final = first_ev(EV_FINAL);
    int finish = first_ev(EV_FINISH);
    int wait = first_ev(EV_WAIT);
    int release = first_ev(EV_RELEASE);
    bool gpu_done_before_final = (finish >= 0 && (final < 0 || finish < final)) &&
                                 (wait < 0 || final < 0 || wait < final);
    if (!gpu_done_before_final) {
        printf("FAIL mapper-uninit-order: GPU completion not before final ref "
               "(final=%d finish=%d wait=%d release=%d)\n", final, finish, wait, release);
        return 1;
    }
    if (release < 0) {
        printf("FAIL mapper-uninit-order: buffer was never returned\n");
        return 1;
    }
    printf("PASS mapper-uninit-order\n");
    return 0;
}

static int mode_mapper_teardown_release_error(void) {
#ifdef PHASE28
    struct ra_hwdec_mapper mapper = {0};
    struct ohcodec_priv owner = {0};
    struct ohcodec_mapper_priv mp = {0};
    struct mp_image *img = calloc(1, sizeof(*img));
    struct ohcodec_interop interop = {0};
    struct ohcodec_surface surface = { .image = (void *)(uintptr_t)0x55 };
    struct ra_hwdec hw = {0};
    hw.priv = &owner;
    owner.interop = &interop;
    owner.surface = &surface;
    mapper.owner = &hw;
    mapper.priv = &mp;
    mp.last_token = (AVOHCodecBuffer *)(uintptr_t)0x200;
    mp.last_src = img;
    make_vk(&mapper, &mp);
    interop.drain = ohcodec_drain;
    interop.release = mapper_release;
    interop.mapper_init = fake_mapper_init;
    interop.mapper_uninit = vk_mapper_uninit;
    release_result = -123;
    mapper_uninit(&mapper);
    release_result = NATIVE_ERROR_OK;
    bool invalid = owner.surface_invalid;
    struct ra_hwdec_mapper next = { .owner = &hw };
    struct ohcodec_mapper_priv next_mp = {0};
    next.priv = &next_mp;
    int init_ret = mapper_init(&next);
    dump_events();
    if (!invalid || init_ret == 0) {
        printf("FAIL mapper-teardown-release-error: invalid=%d init=%d\n",
               invalid, init_ret);
        return 1;
    }
    printf("PASS mapper-teardown-release-error\n");
    return 0;
#else
    printf("FAIL mapper-teardown-release-error: baseline has no generic "
           "release-error latch\n");
    return 1;
#endif
}

static int mode_surface_owner_invalid(void) {
#ifdef PHASE28
    struct ohcodec_priv owner = { .surface_invalid = true };
    struct ra_hwdec_driver drv = { .device_type = AV_HWDEVICE_TYPE_OHCODEC };
    struct ra_hwdec hw = { .driver = &drv, .priv = &owner };
    struct ra_hwdec *list[1] = { &hw };
    bool found = ohcodec_hwdec_find(list, 1) == &hw;
    bool invalid = ohcodec_hwdec_surface_invalid(&hw);
    struct ra_hwdec_mapper mapper = { .owner = &hw };
    struct ohcodec_mapper_priv mp = {0};
    mapper.priv = &mp;
    int init_ret = mapper_init(&mapper);
    if (!found || !invalid || init_ret == 0) {
        printf("FAIL surface-owner-invalid: found=%d invalid=%d init=%d\n",
               found, invalid, init_ret);
        return 1;
    }
    printf("PASS surface-owner-invalid\n");
    return 0;
#else
    printf("FAIL surface-owner-invalid: baseline has no persistent owner query\n");
    return 1;
#endif
}

static int fake_hw_uninit_calls, fake_mapper_uninit_calls;
static void fake_hw_uninit(struct ra_hwdec *hw) { (void)hw; fake_hw_uninit_calls++; }
static void fake_mapper_uninit(struct ra_hwdec_mapper *mapper) { (void)mapper; fake_mapper_uninit_calls++; }

static int mode_unsafe_outer_free(void) {
#ifdef PHASE28
    struct ra_hwdec_mapper mapper = {0};
    struct ohcodec_priv owner = {0};
    struct ohcodec_mapper_priv mp = {0};
    struct mp_image *img = calloc(1, sizeof(*img));
    struct ohcodec_interop interop = {0};
    struct ohcodec_surface surface = { .image = (void *)(uintptr_t)0x55 };
    struct ra_hwdec_driver drv = { .device_type = AV_HWDEVICE_TYPE_OHCODEC,
                                   .uninit = fake_hw_uninit };
    struct ra_hwdec_mapper_driver mdrv = { .uninit = mapper_uninit };
    struct ra_hwdec hw = { .driver = &drv, .priv = &owner };
    owner.interop = &interop;
    owner.surface = &surface;
    mapper.owner = &hw;
    mapper.driver = &mdrv;
    mapper.priv = &mp;
    mp.last_token = (AVOHCodecBuffer *)(uintptr_t)0x200;
    mp.last_src = img;
    make_vk(&mapper, &mp);
    interop.drain = ohcodec_drain;
    interop.release = mapper_release;
    interop.mapper_init = fake_mapper_init;
    interop.mapper_uninit = fake_mapper_uninit;
    queue_wait_result = (VkResult)-4;
    struct ra_hwdec_mapper *mapper_p = &mapper;
    ra_hwdec_mapper_free(&mapper_p);
    ra_hwdec_uninit(&hw);
    queue_wait_result = VK_SUCCESS;
    dump_events();
    if (!owner.surface_invalid || !hw.resource_retained ||
        mapper_p != NULL || fake_mapper_uninit_calls != 0 ||
        fake_hw_uninit_calls != 0) {
        printf("FAIL unsafe-outer-free: invalid=%d retained=%d mapper=%p "
               "mapper_uninit=%d hw_uninit=%d\n", owner.surface_invalid,
               hw.resource_retained, (void *)mapper_p, fake_mapper_uninit_calls,
               fake_hw_uninit_calls);
        return 1;
    }
    printf("PASS unsafe-outer-free\n");
    return 0;
#else
    printf("FAIL unsafe-outer-free: baseline frees mapper after UNSAFE\n");
    return 1;
#endif
}

static int mode_empty_current_drain(void) {
    struct ra_hwdec_mapper mapper = {0};
    struct ohcodec_priv owner = {0};
    struct ohcodec_mapper_priv mp = {0};
    struct mp_image *img = calloc(1, sizeof(*img));
    struct ohcodec_interop interop = {0};
    struct ohcodec_surface surface = { .image = (void *)(uintptr_t)0x55 };
    struct ra_hwdec hw = {0};
    hw.priv = &owner;
    owner.interop = &interop;
    owner.surface = &surface;
    mapper.owner = &hw;
    mapper.priv = &mp;
    mp.last_token = (AVOHCodecBuffer *)(uintptr_t)0x200;
    mp.last_src = img;
    struct vk_mapper *v = make_vk(&mapper, &mp);
    struct vk_import *e = v->current;
    v->imports = e;              /* historical external release, current to be cleared */
    v->num_imports = 1;
    interop.release = mapper_release;
    interop.mapper_uninit = vk_mapper_uninit;
#ifdef PHASE28
    interop.drain = ohcodec_drain;
    mapper_release(&mapper);
    int result = ohcodec_drain(&mapper, OHCODEC_DRAIN_REASON_CLOSE, NULL);
    dump_events();
    int wait = first_ev(EV_WAIT), destroy = first_ev(EV_DESTROY);
    if (result != OHCODEC_DRAIN_SAFE || wait < 0 ||
        (destroy >= 0 && wait > destroy)) {
        printf("FAIL empty-current-drain: result=%d wait=%d destroy=%d\n",
               result, wait, destroy);
        return 1;
    }
    printf("PASS empty-current-drain\n");
    return 0;
#else
    (void)v; (void)e;
    mapper_release(&mapper);
    vk_mapper_uninit(&mapper);
    dump_events();
    int wait = first_ev(EV_WAIT), destroy = first_ev(EV_DESTROY);
    if (wait >= 0 && (destroy < 0 || wait < destroy)) {
        printf("FAIL empty-current-drain: baseline unexpectedly waited\n");
        return 1;
    }
    printf("FAIL empty-current-drain: baseline destroyed imports without "
           "waiting for historical external release (wait=%d destroy=%d)\n",
           wait, destroy);
    return 1;
#endif
}

static int mode_vd_preflight(void) {
    struct mp_filter vd = {0};
    struct vd_ffmpeg_ctx ctx = {0};
    struct vo vo = {0};
    struct vo_internal in = {0};
    struct vo_driver drv = { .control = fake_driver_control, .name = "gpu-next" };
    mp_cond_init(&in.wakeup);
    vo.in = &in;
    vo.driver = &drv;
    AVCodecContext *avctx = calloc(1, sizeof(*avctx));
    vd.priv = &ctx;
    ctx.avctx = avctx;
    ctx.use_hwdec = true;
    snprintf(ctx.hwdec.name, sizeof(ctx.hwdec.name), "hevc_ohcodec-ohcodec");
    ctx.hwdec.lavc_device = AV_HWDEVICE_TYPE_OHCODEC;
    ctx.vo = &vo;
    reset_avctx(&vd);
    dump_events();
    int pre = first_ev(EV_PREFLIGHT);
    int flush = first_ev(EV_FLUSH);
    if (pre < 0 || (flush >= 0 && pre > flush)) {
        printf("FAIL vd-lavc-preflight: no synchronous preflight before flush "
               "(preflight=%d flush=%d)\n", pre, flush);
        return 1;
    }
    printf("PASS vd-lavc-preflight\n");
    return 0;
}

static int mode_vd_uninit(void) {
    struct mp_filter vd = {0};
    struct vd_ffmpeg_ctx ctx = {0};
    struct vo vo = {0};
    struct vo_internal in = {0};
    struct vo_driver drv = { .control = fake_driver_control, .name = "gpu-next" };
    mp_cond_init(&in.wakeup);
    vo.in = &in;
    vo.driver = &drv;
    AVCodecContext *avctx = calloc(1, sizeof(*avctx));
    vd.priv = &ctx;
    ctx.avctx = avctx;
    ctx.use_hwdec = true;
    snprintf(ctx.hwdec.name, sizeof(ctx.hwdec.name), "hevc_ohcodec-ohcodec");
    ctx.hwdec.lavc_device = AV_HWDEVICE_TYPE_OHCODEC;
    ctx.vo = &vo;
    uninit_avctx(&vd);
    dump_events();
    int pre = first_ev(EV_PREFLIGHT);
    int free_ev = first_ev(EV_FREE);
    if (pre < 0 || (free_ev >= 0 && pre > free_ev)) {
        printf("FAIL vd-lavc-preflight-uninit: preflight must precede free "
               "(preflight=%d free=%d)\n", pre, free_ev);
        return 1;
    }
    printf("PASS vd-lavc-preflight-uninit\n");
    return 0;
}

static int mode_vo_control(void) {
    struct vo_internal in = {0};
    struct vo vo = {0};
    struct vo_ohcodec_drain_req req = {0};
    struct vo_driver drv = { .control = fake_driver_control, .name = "gpu-next" };
    in.lock = (mp_mutex){0};
    mp_cond_init(&in.wakeup);
    in.current_frame = calloc(1, sizeof(struct vo_frame));
    in.frame_queued = calloc(1, sizeof(struct vo_frame));
    in.hasframe = true;
    in.hasframe_rendered = true;
    vo.in = &in;
    vo.driver = &drv;
    int ret = vo_control(&vo, VOCTRL_OHCODEC_DRAIN, &req);
    dump_events();
    bool cleared = !driver_saw_current && !driver_saw_queued && !in.current_frame && !in.frame_queued;
    if (ret != 0 || req.result != VO_OHCODEC_DRAIN_SAFE || !cleared) {
        printf("FAIL vo-drain-control: ret=%d result=%d saw_current=%d saw_queued=%d\n",
               ret, req.result, driver_saw_current, driver_saw_queued);
        return 1;
    }
    printf("PASS vo-drain-control\n");
    return 0;
}

#ifdef PHASE28
static int mode_unsafe_preflight(void) {
    struct mp_filter vd = {0};
    struct vd_ffmpeg_ctx ctx = {0};
    struct vo vo = {0};
    struct vo_internal in = {0};
    struct vo_driver drv = { .control = fake_driver_control, .name = "gpu-next" };
    mp_cond_init(&in.wakeup);
    vo.in = &in;
    vo.driver = &drv;
    AVCodecContext *avctx = calloc(1, sizeof(*avctx));
    vd.priv = &ctx;
    ctx.avctx = avctx;
    ctx.use_hwdec = true;
    snprintf(ctx.hwdec.name, sizeof(ctx.hwdec.name), "hevc_ohcodec-ohcodec");
    ctx.hwdec.lavc_device = AV_HWDEVICE_TYPE_OHCODEC;
    ctx.vo = &vo;
    driver_result = VO_OHCODEC_DRAIN_UNSAFE;
    bool ok = ohcodec_lifecycle_preflight(&vd, VO_OHCODEC_DRAIN_REASON_CLOSE);
    driver_result = VO_OHCODEC_DRAIN_SAFE;
#ifdef MP_OHCODEC_LIFECYCLE_EXPERIMENT
    (void)ok;
    printf("FAIL unsafe-preflight: experiment build returned instead of abort\n");
    return 1;
#else
    if (ok || !ctx.lifecycle_unsafe) {
        printf("FAIL unsafe-preflight: normal build did not quarantine "
               "(ok=%d unsafe=%d)\n", ok, ctx.lifecycle_unsafe);
        return 1;
    }
    printf("PASS unsafe-preflight-quarantine\n");
    return 0;
#endif
}

#endif

static int mode_hang(void) {
    /* Test-only sleep used to prove the external watchdog timeout path. */
    sleep(60);
    return 0;
}

static int mode_surface_invalid_reinit(void) {
#ifdef PHASE28
    struct mp_filter vd = {0};
    struct vd_ffmpeg_ctx ctx = {0};
    struct vo vo = {0};
    struct vo_internal in = {0};
    struct vo_driver drv = { .control = fake_driver_control, .name = "gpu-next" };
    mp_cond_init(&in.wakeup);
    vo.in = &in;
    vo.driver = &drv;
    AVCodecContext *avctx = calloc(1, sizeof(*avctx));
    vd.priv = &ctx;
    ctx.avctx = avctx;
    ctx.use_hwdec = true;
    snprintf(ctx.hwdec.name, sizeof(ctx.hwdec.name), "hevc_ohcodec-ohcodec");
    ctx.hwdec.lavc_device = AV_HWDEVICE_TYPE_OHCODEC;
    ctx.vo = &vo;
    surface_invalid = 0; surface_marks = 0; surface_queries = 0;
    driver_result = VO_OHCODEC_DRAIN_SAFE_RELEASE_ERROR;
    reset_avctx(&vd);
    bool refused = ohcodec_lifecycle_refuse_init(&ctx);
    /* A new decoder filter on the same VO must be refused too. */
    struct vd_ffmpeg_ctx next = { .use_hwdec = true, .vo = &vo };
    next.hwdec.lavc_device = AV_HWDEVICE_TYPE_OHCODEC;
    bool next_refused = ohcodec_lifecycle_refuse_init(&next);
    driver_result = VO_OHCODEC_DRAIN_SAFE;
    dump_events();
    if (!refused || !ctx.lifecycle_failed || !surface_invalid ||
        surface_marks != 1 || !next_refused || !next.lifecycle_failed) {
        printf("FAIL surface-invalid-reinit: refused=%d failed=%d invalid=%d "
               "marks=%d next_refused=%d next_failed=%d\n",
               refused, ctx.lifecycle_failed, surface_invalid, surface_marks,
               next_refused, next.lifecycle_failed);
        return 1;
    }
    printf("PASS surface-invalid-reinit\n");
    return 0;
#else
    printf("FAIL surface-invalid-reinit: baseline has no terminal Surface state\n");
    return 1;
#endif
}

static int mode_eof_deferred(void) {
    struct mp_filter vd = {0};
    struct vd_ffmpeg_ctx ctx = {0};
    struct vo vo = {0};
    struct vo_internal in = {0};
    struct vo_driver drv = { .control = fake_driver_control, .name = "gpu-next" };
    mp_cond_init(&in.wakeup);
    vo.in = &in;
    vo.driver = &drv;
    AVCodecContext *avctx = calloc(1, sizeof(*avctx));
    AVFrame *pic = calloc(1, sizeof(*pic));
    vd.priv = &ctx;
    ctx.avctx = avctx;
    ctx.pic = pic;
    ctx.use_hwdec = true;
    snprintf(ctx.hwdec.name, sizeof(ctx.hwdec.name), "hevc_ohcodec-ohcodec");
    ctx.hwdec.lavc_device = AV_HWDEVICE_TYPE_OHCODEC;
    ctx.vo = &vo;
    int ret = decode_frame(&vd);
    dump_events();
    int pre = first_ev(EV_PREFLIGHT), flush = first_ev(EV_FLUSH);
    if (ret != AVERROR_EOF || pre >= 0 || flush >= 0 || !ctx.eof_deferred) {
        printf("FAIL eof-deferred: EOF reset not deferred (ret=%d preflight=%d flush=%d flag=%d)\n",
               ret, pre, flush, ctx.eof_deferred);
        return 1;
    }
    struct demux_packet pkt = { .size = 1 };
    send_packet(&vd, &pkt);
    dump_events();
    pre = first_ev(EV_PREFLIGHT);
    flush = first_ev(EV_FLUSH);
    int pre_count = 0, flush_count = 0;
    for (int i = 0; i < nevents; i++) { pre_count += events[i] == EV_PREFLIGHT; flush_count += events[i] == EV_FLUSH; }
    if (pre_count != 1 || flush_count != 1 || ctx.eof_deferred) {
        printf("FAIL eof-deferred: new packet did not consume exactly one reset "
               "(preflight=%d flush=%d flag=%d)\n", pre_count, flush_count, ctx.eof_deferred);
        return 1;
    }
    printf("PASS eof-deferred\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 64;
    if (!strcmp(argv[1], "mapper-uninit-order")) return mode_mapper_uninit();
    if (!strcmp(argv[1], "vd-lavc-preflight")) return mode_vd_preflight();
    if (!strcmp(argv[1], "empty-current-drain")) return mode_empty_current_drain();
    if (!strcmp(argv[1], "mapper-teardown-release-error")) return mode_mapper_teardown_release_error();
    if (!strcmp(argv[1], "unsafe-outer-free")) return mode_unsafe_outer_free();
    if (!strcmp(argv[1], "surface-owner-invalid")) return mode_surface_owner_invalid();
    if (!strcmp(argv[1], "vd-lavc-preflight-uninit")) return mode_vd_uninit();
    if (!strcmp(argv[1], "vo-drain-control")) return mode_vo_control();
    if (!strcmp(argv[1], "eof-deferred")) return mode_eof_deferred();
    if (!strcmp(argv[1], "surface-invalid-reinit")) return mode_surface_invalid_reinit();
#ifdef PHASE28
    if (!strcmp(argv[1], "unsafe-preflight")) return mode_unsafe_preflight();
#endif
    if (!strcmp(argv[1], "watchdog-hang")) return mode_hang();
    return 64;
}
