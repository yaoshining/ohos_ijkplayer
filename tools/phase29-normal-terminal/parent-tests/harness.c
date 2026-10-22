/*
 * Phase28 real parent-release-chain harness.
 *
 * Production slices included below are extracted verbatim by extract.py:
 * vo_gpu_next uninit + VOCTRL cases, the OHCodec generic drain path, the
 * libplacebo drain path, the hwdec registry, gpu/hwdec teardown, VO
 * dispatch/destroy and vd_lavc preflight/teardown.  Platform, libplacebo,
 * FFmpeg, talloc and player objects are stubbed; every destruction of a
 * parent/dependency is counted and printed.
 *
 * GREEN criterion for an UNSAFE observation is not "timeout": the process must
 * still be alive because the VO thread is inside the terminal barrier, the
 * barrier line must be emitted, and no parent/dependency destruction event may
 * appear.  Normal and SAFE_RELEASE_ERROR must still complete the original
 * cleanup.  The negative control uses the same test with the barrier removed.
 */
#define _POSIX_C_SOURCE 200809L
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

/* ------------------------------------------------------------------ logs */
#define MP_INFO(obj, ...) do { (void)(obj); fprintf(stdout, __VA_ARGS__); fflush(stdout); } while (0)
#define MP_ERR(obj, ...) do { (void)(obj); fprintf(stderr, __VA_ARGS__); fflush(stderr); } while (0)
#define MP_TRACE(obj, ...) do { (void)(obj); } while (0)
#define MP_VERBOSE(obj, ...) do { (void)(obj); } while (0)
#define MSGL_ERR 2
struct mp_log { int unused; };
static void mp_msg(struct mp_log *log, int lev, const char *fmt, ...)
{
    (void)log; (void)lev;
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fflush(stderr);
}

static int relaxed_assert;
#define mp_assert(x) do { \
    if (!(x)) { \
        fprintf(stderr, "Assertion failed: (%s), function %s, file %s, line %d.\n", \
                #x, __func__, __FILE__, __LINE__); \
        if (relaxed_assert) { \
            fprintf(stderr, "ASSERT_RELAXED %s:%d expr=%s\n", __FILE__, __LINE__, #x); \
        } else { \
            fflush(NULL); \
            abort(); \
        } \
    } \
} while (0)
#define MP_ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define MP_NORETURN __attribute__((noreturn))
#define MP_TARRAY_APPEND(ctx, arr, num, item) do { \
    void *_mp_new = realloc((arr), sizeof(*(arr)) * ((num) + 1)); \
    if (!_mp_new) abort(); \
    (arr) = _mp_new; \
    (arr)[(num)++] = (item); \
} while (0)
#define MP_TARRAY_REMOVE_AT(arr, num, idx) do { \
    memmove(&(arr)[(idx)], &(arr)[(idx) + 1], sizeof(*(arr)) * ((num) - (idx) - 1)); \
    (num)--; \
} while (0)

/* ------------------------------------------------------------- counters */
static atomic_int c_queue_destroy, c_queue_reset, c_gpu_ctx_destroy;
static atomic_int c_registry_destroy, c_registry_add, c_registry_remove;
static atomic_int c_dr_helper_free, c_parent_vo_free, c_parent_other_free;
static atomic_int c_mapper_free, c_owner_free, c_owner_uninit;
static atomic_int c_avctx_free, c_avctx_quarantine, c_filter_free;
static atomic_int c_barrier, c_uninit_begin, c_uninit_end, c_vo_destroy_end;
static atomic_int c_import_destroy, c_frame_final;
static atomic_int c_mpctx_free, c_mconfig_free, c_abort_list_free;
static atomic_int c_osd_free, c_input_free, c_clipboard_free, c_global_free;
static atomic_int c_clients_free, c_command_free, c_encoder_free, c_ipc_free;
static atomic_int c_audio_out_free, c_video_chain_uninit, c_msg_uninit;
static atomic_int c_destroy_events;
static atomic_int c_texture_destroy, c_renderer_destroy, c_options_destroy;
static atomic_int c_cache_destroy, c_icc_destroy, c_lut_destroy;
static atomic_int c_shader_destroy, c_vk_mapper_free;
static pthread_mutex_t event_lock = PTHREAD_MUTEX_INITIALIZER;

static void event(const char *fmt, ...)
{
    va_list ap;
    pthread_mutex_lock(&event_lock);
    va_start(ap, fmt);
    vfprintf(stdout, fmt, ap);
    va_end(ap);
    fputc('\n', stdout);
    fflush(stdout);
    pthread_mutex_unlock(&event_lock);
}

static void destroy_event(const char *name, atomic_int *counter)
{
    atomic_fetch_add(counter, 1);
    atomic_fetch_add(&c_destroy_events, 1);
    event("EVENT %s", name);
}

/* -------------------------------------------------------------- talloc */
static void *observed_vo;
static void *observed_mapper;
static void *observed_owner;
static void *observed_devs;
static void *observed_hwdecs;
static void *observed_mpctx;
static void *observed_mconfig;
static void *observed_abort_list;

#define talloc_zero(ctx, type) ((type *)calloc(1, sizeof(type)))
#define talloc_zero_size(ctx, size) calloc(1, (size))
static int talloc_free(void *p)
{
    if (!p)
        return 0;
    if (p == observed_vo) {
        destroy_event("parent-vo-free", &c_parent_vo_free);
        return 0; /* the test owns this object on the stack/heap */
    }
    if (p == observed_mapper) {
        destroy_event("mapper-free", &c_mapper_free);
        return 0;
    }
    if (p == observed_owner) {
        destroy_event("owner-free", &c_owner_free);
        return 0;
    }
    if (p == observed_devs) {
        destroy_event("destroy-registry", &c_registry_destroy);
        free(p);
        return 0;
    }
    if (p == observed_mpctx) {
        atomic_fetch_add(&c_parent_other_free, 1);
        destroy_event("parent-mpctx-free", &c_mpctx_free);
        return 0;
    }
    if (p == observed_mconfig) {
        destroy_event("parent-mconfig-free", &c_mconfig_free);
        free(p);
        return 0;
    }
    if (p == observed_abort_list) {
        destroy_event("parent-abort-list-free", &c_abort_list_free);
        free(p);
        return 0;
    }
    if (p == observed_hwdecs) {
        free(p);
        return 0;
    }
    free(p);
    return 0;
}
#define talloc(ctx, type) ((type *)calloc(1, sizeof(type)))
#define talloc_ptrtype(ctx, ptr) ((__typeof__(ptr))calloc(1, sizeof(*(ptr))))
#define talloc_memdup(ctx, src, size) ({ void *_p = malloc(size); memcpy(_p, src, size); _p; })
#define TA_FREEP(p) do { \
    if (*(p)) { free(*(p)); *(p) = NULL; \
                destroy_event("dr_helper-free", &c_dr_helper_free); } \
} while (0)

/* --------------------------------------------------------------- mutex */
typedef pthread_mutex_t mp_mutex;
typedef pthread_cond_t mp_cond;
static int mp_mutex_init(mp_mutex *m) { return pthread_mutex_init(m, NULL); }
static void mp_mutex_destroy(mp_mutex *m) { pthread_mutex_destroy(m); }
static void mp_mutex_lock(mp_mutex *m) { pthread_mutex_lock(m); }
static void mp_mutex_unlock(mp_mutex *m) { pthread_mutex_unlock(m); }
static void mp_cond_init(mp_cond *c) { pthread_cond_init(c, NULL); }
static void mp_cond_destroy(mp_cond *c) { pthread_cond_destroy(c); }
static void mp_cond_signal(mp_cond *c) { pthread_cond_signal(c); }
static void mp_cond_broadcast(mp_cond *c) { pthread_cond_broadcast(c); }
static int mp_cond_timedwait(mp_cond *c, mp_mutex *m, int64_t ns)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += ns / 1000000000;
    ts.tv_nsec += ns % 1000000000;
    if (ts.tv_nsec >= 1000000000) { ts.tv_sec++; ts.tv_nsec -= 1000000000; }
    return pthread_cond_timedwait(c, m, &ts);
}
static int mp_cond_wait(mp_cond *c, mp_mutex *m) { return pthread_cond_wait(c, m); }
static int64_t mp_time_ns(void);
static int mp_cond_timedwait_until(mp_cond *c, mp_mutex *m, int64_t until)
{
    int64_t rel = until - mp_time_ns();
    return mp_cond_timedwait(c, m, rel > 0 ? rel : 0);
}
static int64_t mp_time_ns_add(int64_t time_ns, double timeout_sec)
{
    return time_ns + (int64_t)(timeout_sec * 1e9);
}
#define MP_TIME_S_TO_NS(x) ((int64_t)((x) * 1e9))
#define MPMIN(a, b) ((a) < (b) ? (a) : (b))
#define MPMAX(a, b) ((a) > (b) ? (a) : (b))
#define MP_THREAD_VOID void *
#define MP_THREAD_RETURN() return NULL
#define mp_thread_current_id() pthread_self()
static void mp_thread_set_name(const char *name) { (void)name; }
static intptr_t mp_rendezvous(void *tag, intptr_t value) { (void)tag; return value; }
#define talloc_set_destructor(p, fn) do { (void)(p); } while (0)
static int64_t mp_time_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}
static void mp_thread_join(pthread_t t) { pthread_join(t, NULL); }

/* --------------------------------------------------------- base types */
typedef struct { int unused; } OHNativeWindow;
typedef struct { int unused; } OHNativeWindowBuffer;
typedef struct { int unused; } OH_NativeBuffer;
typedef struct { int unused; } OH_NativeImage;
typedef struct { int unused; } AVOHCodecBuffer;
typedef struct { int unused; } AVBufferRef;
typedef struct { int unused; } AVPacket;
typedef struct { int unused; } AVFrame;
typedef struct { int width, height; } AVCodecContext;
typedef struct { int unused; } OH_AVFormat;
struct pl_log; struct pl_gpu; struct pl_tex; struct pl_fmt; struct pl_buf;
struct pl_queue; struct pl_renderer; struct pl_swapchain; struct pl_options;
struct pl_icc_object; struct pl_shader_info; struct pl_hook; struct pl_custom_lut;
typedef struct pl_log *pl_log;
typedef struct pl_gpu *pl_gpu;
typedef struct pl_tex *pl_tex;
typedef struct pl_fmt *pl_fmt;
typedef struct pl_buf *pl_buf;
typedef struct pl_queue *pl_queue;
typedef struct pl_renderer *pl_renderer;
typedef struct pl_swapchain *pl_swapchain;
typedef struct pl_options *pl_options;
typedef struct pl_icc_object *pl_icc_object;
typedef struct pl_shader_info *pl_shader_info;
typedef struct pl_hook *pl_hook;
typedef struct pl_custom_lut *pl_custom_lut;
typedef void *VkDevice;
typedef uint64_t VkSemaphore;
typedef uint64_t VkImage;
typedef void *VkImageView;
typedef void *VkDeviceMemory;
typedef int VkResult;
#define VK_SUCCESS 0
#define VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL 5
#define VK_QUEUE_FAMILY_EXTERNAL 0xffffffffu
#define NATIVE_ERROR_OK 0
#define NATIVE_ERROR_NO_BUFFER (-1)
#define IMGFMT_OHCODEC 200
#define AV_HWDEVICE_TYPE_OHCODEC 100
#define VO_PASS_PERF_MAX 1
#define MAX_OSD_PARTS 1
#define VO_MAX_REQ_FRAMES 3

struct mpv_global { int unused; };
struct m_config_cache { int unused; };
struct input_ctx { int unused; };
struct osd_state { int unused; };
struct encode_lavc_context { int unused; };
struct stats_ctx { int unused; };
struct gpu_ctx { int unused; };
struct ra_ctx { int unused; };
struct ra { int unused; };
struct ra_tex { int unused; };
struct mp_image { int id; int imgfmt; void *planes[4]; };
static void mp_image_unrefp(struct mp_image **p)
{
    if (*p) {
        atomic_fetch_add(&c_frame_final, 1);
        free(*p);
        *p = NULL;
    }
}

/* --------------------------------------------------------- FFmpeg stubs */
enum AVHWDeviceType { AV_HWDEVICE_TYPE_NONE = 0, AV_HWDEVICE_TYPE_OTHER = 1 };
#define AV_HWDEVICE_TYPE_OHCODEC 100
typedef struct vd_ffmpeg_ctx vd_ffmpeg_ctx;
static void av_buffer_unref(AVBufferRef **r) { if (r && *r) { free(*r); *r = NULL; } }
static int avcodec_is_open(AVCodecContext *a) { return a != NULL; }
static void avcodec_flush_buffers(AVCodecContext *a) { (void)a; }
static void av_frame_free(AVFrame **f) { free(*f); *f = NULL; }
static void mp_free_av_packet(AVPacket **p) { free(*p); *p = NULL; }
static void avcodec_free_context(AVCodecContext **a)
{
    destroy_event("avctx-free", &c_avctx_free);
    free(*a);
    *a = NULL;
}

/* ------------------------------------------------------ registry types */
struct hwdec_imgfmt_request { int imgfmt; };
struct mp_hwdec_ctx {
    const char *driver_name;
    AVBufferRef *av_device_ref;
    int hw_imgfmt;
};
struct mp_hwdec_devices {
    mp_mutex lock;
    struct mp_hwdec_ctx **hwctxs;
    int num_hwctxs;
    void (*load_api)(void *ctx, struct hwdec_imgfmt_request *params);
    void *load_api_ctx;
};

/* ---------------------------------------------------------- hwdec types */
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
    int (*drain)(struct ra_hwdec_mapper *, int reason, int *platform_error);
};
struct ohcodec_surface {
    OH_NativeImage *image;
    OHNativeWindow *window;
    mp_mutex lock;
    mp_cond cond;
    unsigned pending;
    bool initialized;
};
struct ohcodec_priv {
    struct mp_hwdec_ctx hwctx;
    struct ohcodec_surface *surface;
    void *interop_owner_priv;
    const struct ohcodec_interop *interop;
    bool surface_invalid;
#ifdef MP_OHCODEC_DIAGNOSTIC
    uint64_t diagnostic_owner;
    uint64_t diagnostic_consumer;
#endif
};
struct ohcodec_mapper_priv {
    void *priv;
    AVOHCodecBuffer *last_token;
    int terminal_drain_error;
    struct mp_image *last_src;
};
struct ra_hwdec {
    const struct ra_hwdec_driver *driver;
    void *priv;
    struct mp_log *log;
    struct mp_hwdec_devices *devs;
    bool resource_retained;
};
struct ra_hwdec_mapper {
    const struct ra_hwdec_mapper_driver *driver;
    struct mp_log *log;
    struct ra *ra;
    void *priv;
    struct ra_hwdec *owner;
    bool resource_retained;
    struct mp_image *src;
    struct ra_tex *tex[4];
};
struct ra_hwdec_mapper_driver {
    size_t priv_size;
    int (*init)(struct ra_hwdec_mapper *);
    void (*uninit)(struct ra_hwdec_mapper *);
    int (*map)(struct ra_hwdec_mapper *);
    void (*unmap)(struct ra_hwdec_mapper *);
};
struct ra_hwdec_driver {
    const char *name;
    size_t priv_size;
    int imgfmts[3];
    enum AVHWDeviceType device_type;
    int (*init)(struct ra_hwdec *);
    void (*uninit)(struct ra_hwdec *);
    const struct ra_hwdec_mapper_driver *mapper;
};
struct ra_hwdec_ctx {
    struct mp_log *log;
    struct mpv_global *global;
    struct ra_ctx *ra_ctx;
    bool loading_done;
    struct ra_hwdec **hwdecs;
    int num_hwdecs;
};

/* ------------------------------------------------------- Vulkan types */
struct vk_import {
    struct vk_import *next;
    uint32_t seq;
    void *native_buffer;
    VkImage image;
    VkSemaphore acquire_sem;
    VkSemaphore release_sem;
    VkImageView view;
    VkDeviceMemory memory;
    pl_tex pltex;
    void *ratex;
    bool busy;
};
struct pl_vulkan {
    VkDevice device;
    void (*lock_queue)(struct pl_vulkan *, uint32_t qf, uint32_t index);
    void (*unlock_queue)(struct pl_vulkan *, uint32_t qf, uint32_t index);
};
struct vk_mapper {
    pl_gpu gpu;
    struct pl_vulkan *vk;
    void *get_props;
    void *acquire_image;
    VkResult (*signal_release)(void *queue, uint32_t n, VkSemaphore *sem,
                               VkImage image, int *fence_fd);
    VkResult (*wait_idle)(void *queue);
    void *queue;
    uint32_t qf;
    pl_fmt rgba8;
    pl_fmt rgba16;
    struct vk_import *imports;
    int num_imports;
    struct vk_import *current;
    OHNativeWindowBuffer *window_buffer;
    const char *release_reason;
    bool external_release_inflight;
};
struct pl_vulkan_hold_params {
    pl_tex tex;
    int layout;
    uint32_t qf;
    struct { VkSemaphore sem; } semaphore;
};
#define pl_vulkan_hold_params(...) ((struct pl_vulkan_hold_params){ __VA_ARGS__ })

/* ---------------------------------------------------------- libplacebo */
static int hold_calls;
static bool hold_ok = true;
static bool pl_vulkan_hold_ex(pl_gpu gpu, struct pl_vulkan_hold_params p)
{
    (void)gpu; (void)p;
    hold_calls++;
    return hold_ok;
}
static void pl_gpu_finish(pl_gpu gpu) { (void)gpu; }
static void pl_queue_destroy(pl_queue *q) { (void)q; destroy_event("destroy-queue", &c_queue_destroy); }
static void pl_queue_reset(pl_queue q) { (void)q; atomic_fetch_add(&c_queue_reset, 1); event("EVENT reset-queue"); }
static void pl_tex_destroy(pl_gpu gpu, pl_tex *tex) { (void)gpu; if (tex) *tex = NULL; destroy_event("destroy-texture", &c_texture_destroy); }
static void ra_tex_free(struct ra *ra, void **tex) { (void)ra; if (tex) *tex = NULL; }
static void vkDestroySemaphore(VkDevice d, VkSemaphore s, const void *a) { (void)d; (void)s; (void)a; }
static void vkDestroyImageView(VkDevice d, VkImageView v, const void *a) { (void)d; (void)v; (void)a; }
static void vkDestroyImage(VkDevice d, VkImage i, const void *a) { (void)d; (void)i; (void)a; }
static void vkFreeMemory(VkDevice d, VkDeviceMemory m, const void *a) { (void)d; (void)m; (void)a; }
static void OH_NativeBuffer_Unreference(OH_NativeBuffer *b) { (void)b; }
static void pl_lut_free(void *lut) { (void)lut; destroy_event("destroy-lut", &c_lut_destroy); }
static void pl_icc_close(pl_icc_object *icc) { (void)icc; destroy_event("destroy-icc", &c_icc_destroy); }
static void pl_renderer_destroy(pl_renderer *rr) { (void)rr; destroy_event("destroy-renderer", &c_renderer_destroy); }
static void pl_shader_info_deref(pl_shader_info **s) { (void)s; destroy_event("destroy-shader", &c_shader_destroy); }
static void pl_options_free(pl_options *p) { (void)p; destroy_event("destroy-options", &c_options_destroy); }
static void pl_mpv_user_shader_destroy(const struct pl_hook **hook) { (void)hook; }
static void cache_uninit(void *p, void *c) { (void)p; (void)c; destroy_event("destroy-cache", &c_cache_destroy); }
static void gpu_ctx_destroy(struct gpu_ctx **ctx)
{
    if (ctx && *ctx) { destroy_event("destroy-gpu-ctx", &c_gpu_ctx_destroy); free(*ctx); *ctx = NULL; }
}

/* -------------------------------------------------- platform/FFmpeg stubs */
static int release_result = NATIVE_ERROR_OK;
static int OH_NativeImage_ReleaseNativeWindowBuffer(OH_NativeImage *image,
        OHNativeWindowBuffer *b, int fence)
{
    (void)image; (void)b; (void)fence;
    return release_result;
}
static void OH_NativeWindow_NativeObjectUnreference(OHNativeWindowBuffer *b) { (void)b; }
static int OH_NativeBuffer_FromNativeWindowBuffer(OHNativeWindowBuffer *b,
                                                  OH_NativeBuffer **n)
{
    (void)b; *n = (OH_NativeBuffer *)b; return NATIVE_ERROR_OK;
}
static uint32_t OH_NativeBuffer_GetSeqNum(OH_NativeBuffer *n) { return (uint32_t)(uintptr_t)n; }

/* ----------------------------------------------------- dispatch/VO types */
struct vo;
struct mp_dispatch_queue;
typedef void (*mp_dispatch_fn)(void *data);
typedef pthread_t mp_thread_id;
struct mp_dispatch_item {
    mp_dispatch_fn fn;
    void *fn_data;
    bool asynchronous;
    bool mergeable;
    bool completed;
    struct mp_dispatch_item *next;
};
struct mp_dispatch_queue {
    struct mp_dispatch_item *head, *tail;
    mp_mutex lock;
    mp_cond cond;
    void (*wakeup_fn)(void *wakeup_ctx);
    void *wakeup_ctx;
    void (*onlock_fn)(void *onlock_ctx);
    void *onlock_ctx;
    int64_t wait;
    bool interrupted;
    bool in_process;
    mp_thread_id in_process_thread_id;
    bool locked;
    size_t lock_requests;
    bool locked_explicit;
    mp_thread_id locked_explicit_thread_id;
};
struct vo_frame { int id; double pts; double duration; };
struct dr_helper { int unused; };
struct vo_internal {
    mp_mutex lock;
    mp_cond wakeup;
    bool need_wakeup;
    bool terminate;
    bool hasframe;
    bool hasframe_rendered;
    bool request_redraw;
    bool want_redraw;
    bool send_reset;
    bool paused;
    bool rendering;
    bool wakeup_on_done;
    int64_t wakeup_pts;
    struct vo_frame *current_frame;
    struct vo_frame *frame_queued;
    uint64_t current_frame_id;
    double display_fps;
    struct mp_dispatch_queue *dispatch;
    pthread_t thread;
    struct dr_helper *dr_helper;
    struct stats_ctx *stats;
    bool dropped_frame;
};
struct vo_driver {
    const char *name;
    int (*get_image)(struct vo *, struct vo_frame *);
    int (*preinit)(struct vo *);
    int (*control)(struct vo *, uint32_t, void *);
    void (*uninit)(struct vo *);
    void (*draw_frame)(struct vo *, struct vo_frame *);
    void (*flip_page)(struct vo *);
    int caps;
};
struct mp_vo_opts { int unused; };
struct vo {
    struct mp_log *log;
    const struct vo_driver *driver;
    struct mpv_global *global;
    struct vo_internal *in;
    void *priv;
    struct mp_hwdec_devices *hwdec_devs;
    struct m_config_cache *opts_cache;
    mp_mutex params_mutex;
    bool want_redraw;
    struct input_ctx *input_ctx;
    struct osd_state *osd;
    struct encode_lavc_context *encode_lavc_ctx;
    struct mp_vo_opts *opts;
    int64_t previous_redraw_time;
};
/* Minimal MPContext for the real player/video.c and player/main.c slices. */
struct mp_client_api { int unused; };
struct clipboard_ctx { int unused; };
struct mp_ipc_ctx { int unused; };
struct m_config { int unused; };
struct mp_abort_list { int unused; };
struct MPContext {
    struct mpv_global *global;
    struct mp_client_api *clients;
    struct osd_state *osd;
    struct input_ctx *input;
    struct clipboard_ctx *clipboard;
    struct encode_lavc_context *encode_lavc_ctx;
    struct mp_ipc_ctx *ipc_ctx;
    struct m_config *mconfig;
    struct mp_abort_list *abort_list;
    int num_abort_list;
    mp_mutex abort_lock;
    struct vo *video_out;
    bool is_cli;
};
struct mp_filter { void *priv; };
struct hwdec_info { int lavc_device; };
struct hwdec_opts { int unused; };
struct mp_codec_params { int unused; };
struct demux_packet { int size; };
struct vd_ffmpeg_ctx {
    struct mp_log *log;
    AVCodecContext *avctx;
    AVFrame *pic;
    AVPacket *avpkt;
    bool use_hwdec;
    struct hwdec_info hwdec;
    bool flushing;
    bool eof_deferred;
    bool lifecycle_unsafe;
    bool lifecycle_release_error;
    bool lifecycle_failed;
    struct vo *vo;
    struct mp_hwdec_devices *hwdec_devs;
    AVBufferRef *hwdec_dev;
    bool hwdec_request_reinit;
    bool hwdec_failed;
    int hwdec_fail_count;
    int num_delay_queue;
    struct mp_image **delay_queue;
    int num_sent_packets;
    struct demux_packet **sent_packets;
    int num_requeue_packets;
    struct demux_packet **requeue_packets;
    bool hw_probing;
    bool force_eof;
    int max_delay_queue;
    AVBufferRef *cached_hw_frames_ctx;
};

/* ---------------------------------------------------- vo_gpu_next priv */
struct osd_entry { pl_tex tex; };
struct osd_state_gpu { struct osd_entry entries[MAX_OSD_PARTS]; };
struct user_hook { const struct pl_hook *hook; };
struct user_lut { char *opt; char *path; int type; pl_custom_lut *lut; };
struct gl_next_opts {
    struct user_lut lut;
    struct user_lut image_lut;
    struct user_lut target_lut;
    int target_hint;
    int target_hint_mode;
    bool target_hint_strict;
    char **raw_opts;
};
struct frame_info { int count; struct { pl_shader_info *shader; } info[VO_PASS_PERF_MAX]; };
struct cache { int unused; };
struct priv {
    struct mp_log *log;
    struct mpv_global *global;
    struct ra_ctx *ra_ctx;
    struct gpu_ctx *context;
    struct ra_hwdec_ctx hwdec_ctx;
    struct ra_hwdec_mapper *hwdec_mapper;
    mp_mutex dr_lock;
    pl_buf *dr_buffers;
    int num_dr_buffers;
    pl_log pllog;
    pl_gpu gpu;
    pl_renderer rr;
    pl_queue queue;
    pl_swapchain sw;
    pl_fmt osd_fmt[1];
    pl_tex *sub_tex;
    int num_sub_tex;
    struct osd_state_gpu osd_state;
    uint64_t osd_sync;
    bool want_reset;
    pl_options pars;
    struct m_config_cache *opts_cache;
    struct m_config_cache *next_opts_cache;
    struct gl_next_opts *next_opts;
    struct cache shader_cache, icc_cache;
    pl_icc_object icc_profile;
    struct user_hook *user_hooks;
    int num_user_hooks;
    struct frame_info perf_fresh;
    struct frame_info perf_redraw;
};

/* -------------------------------------------------------- declarations */
int vo_control(struct vo *vo, int request, void *data);
void mp_dispatch_run(struct mp_dispatch_queue *queue, mp_dispatch_fn fn, void *data);
void vo_ohcodec_retire_frames(struct vo *vo);
#define OHCODEC_DRAIN_NOT_APPLICABLE 0
#define OHCODEC_DRAIN_SAFE 1
#define OHCODEC_DRAIN_SAFE_RELEASE_ERROR 2
#define OHCODEC_DRAIN_UNSAFE 3
#define OHCODEC_DRAIN_REASON_CLOSE 2
#define VO_OHCODEC_DRAIN_NOT_APPLICABLE 0
#define VO_OHCODEC_DRAIN_SAFE 1
#define VO_OHCODEC_DRAIN_SAFE_RELEASE_ERROR 2
#define VO_OHCODEC_DRAIN_UNSAFE 3
#define VO_OHCODEC_DRAIN_REASON_SEEK 1
#define VO_OHCODEC_DRAIN_REASON_CLOSE 2
#define VO_OHCODEC_DRAIN_REASON_REINIT 3
#define VO_OHCODEC_DRAIN_REASON_RESUME 4
void ra_hwdec_mapper_unmap(struct ra_hwdec_mapper *mapper);
void ra_hwdec_mapper_free(struct ra_hwdec_mapper **mapper);
void ra_hwdec_uninit(struct ra_hwdec *hwdec);
void ra_hwdec_ctx_uninit(struct ra_hwdec_ctx *ctx);
int ohcodec_mapper_drain(struct ra_hwdec_mapper *mapper, int reason, int *platform_error);
bool ohcodec_mapper_can_drain(struct ra_hwdec_mapper *mapper);
bool ohcodec_mapper_surface_invalid(struct ra_hwdec_mapper *mapper);
void ohcodec_mapper_mark_surface_invalid(struct ra_hwdec_mapper *mapper);
bool ohcodec_hwdec_surface_invalid(struct ra_hwdec *hw);
void ohcodec_hwdec_mark_surface_invalid(struct ra_hwdec *hw);
struct ra_hwdec *ohcodec_hwdec_find(struct ra_hwdec **hwdecs, int num);
#ifdef MP_OHCODEC_DIAGNOSTIC
/* Production translation-unit state for the exact barrier function. */
static atomic_bool terminal_barrier_entered;
void ohcodec_terminal_barrier(struct mp_log *log, const char *site);
#endif
static void vk_mapper_uninit(struct ra_hwdec_mapper *mapper);
static void fake_pl_uninit(struct ra_hwdec_mapper *mapper)
{
    struct ohcodec_mapper_priv *p = mapper->priv;
    if (p && p->priv) {
        struct vk_mapper *v = p->priv;
        while (v->imports) {
            struct vk_import *e = v->imports;
            v->imports = e->next;
            free(e);
        }
        free(v);
        p->priv = NULL;
        destroy_event("vk-mapper-free", &c_vk_mapper_free);
    }
}
static void update_opts(struct vo *vo) { (void)vo; }
static void forget_frames(struct vo *vo)
{
    struct vo_internal *in = vo->in;
    talloc_free(in->frame_queued);
    in->frame_queued = NULL;
    in->hasframe = false;
    in->hasframe_rendered = false;
}
static void dispatch_wakeup_cb(void *ctx) { (void)ctx; }

/* ------------------------------------------------ real vo_thread stubs */
#define VO_EVENT_WIN_STATE 1
#define MPV_EVENT_VIDEO_RECONFIG 21
#define VOCTRL_PAUSE 0x102
#define VOCTRL_RESUME 0x103
#define VOCTRL_REDRAW 0x104
static struct dr_helper *dr_helper_create(struct mp_dispatch_queue *dispatch,
        void *get_image, void *ctx) { (void)dispatch; (void)get_image; (void)ctx; return NULL; }
static void dr_helper_acquire_thread(struct dr_helper *dr) { (void)dr; }
static struct mp_image *get_image_vo(void *ctx, int imgfmt, int w, int h,
                                     int stride_align, int flags)
{
    (void)ctx; (void)imgfmt; (void)w; (void)h; (void)stride_align; (void)flags;
    return NULL;
}
static void read_opts(struct vo *vo) { (void)vo; }
static void update_display_fps(struct vo *vo) { vo->in->display_fps = 60.0; }
static void vo_event(struct vo *vo, int events) { (void)vo; (void)events; }
static void stats_event(struct stats_ctx *stats, const char *name)
{
    (void)stats; (void)name;
}
static bool render_frame(struct vo *vo) { (void)vo; return false; }
static void wakeup_core(struct vo *vo) { (void)vo; }
static int64_t get_current_frame_end(struct vo *vo) { (void)vo; return -1; }
static void do_redraw(struct vo *vo) { (void)vo; }
static void wait_vo(struct vo *vo, int64_t until_time)
{
    (void)vo;
    int64_t now = mp_time_ns();
    int64_t ns = until_time > now ? until_time - now : 0;
    if (ns > 20000000)
        ns = 20000000;
    struct timespec ts = { .tv_sec = 0, .tv_nsec = ns };
    nanosleep(&ts, NULL);
}
static int fake_preinit(struct vo *vo) { (void)vo; return 0; }

/* ------------------------------------------- real player parent stubs */
static void uninit_video_chain(struct MPContext *mpctx)
{
    (void)mpctx;
    destroy_event("video-chain-uninit", &c_video_chain_uninit);
}
static void mp_notify(struct MPContext *mpctx, int event, void *data)
{
    (void)mpctx; (void)event; (void)data;
}
static void mp_shutdown_clients(struct MPContext *mpctx) { (void)mpctx; }
static void mp_uninit_ipc(struct mp_ipc_ctx *ctx)
{
    (void)ctx;
    destroy_event("parent-ipc-free", &c_ipc_free);
}
static void uninit_audio_out(struct MPContext *mpctx)
{
    (void)mpctx;
    destroy_event("parent-audio-out-free", &c_audio_out_free);
}
static bool encode_lavc_free(struct encode_lavc_context *ctx)
{
    (void)ctx;
    destroy_event("parent-encoder-free", &c_encoder_free);
    return true;
}
static void command_uninit(struct MPContext *mpctx)
{
    (void)mpctx;
    destroy_event("parent-command-free", &c_command_free);
}
static void mp_clients_destroy(struct MPContext *mpctx)
{
    (void)mpctx;
    destroy_event("parent-clients-free", &c_clients_free);
}
static void osd_free(struct osd_state *osd)
{
    (void)osd;
    destroy_event("parent-osd-free", &c_osd_free);
}
static void mp_input_uninit(struct input_ctx *ictx)
{
    (void)ictx;
    destroy_event("parent-input-free", &c_input_free);
}
static void mp_clipboard_destroy(struct clipboard_ctx *cl)
{
    (void)cl;
    destroy_event("parent-clipboard-free", &c_clipboard_free);
}
static bool cas_terminal_owner(struct MPContext *old, struct MPContext *newctx)
{
    (void)old; (void)newctx; return false;
}
static void terminal_uninit(void) { }
static void uninit_libav(struct mpv_global *global)
{
    (void)global;
    destroy_event("parent-global-free", &c_global_free);
}
static void mp_msg_uninit(struct mpv_global *global)
{
    (void)global;
    destroy_event("parent-log-free", &c_msg_uninit);
}

/* VOCTRL ABI shared by vd_lavc, vo.c and vo_gpu_next. */
#define VO_TRUE 1
#define VO_FALSE 0
#define VOCTRL_OHCODEC_DRAIN 0x4f484344
#define VOCTRL_OHCODEC_SURFACE 0x4f484353
#define VOCTRL_CHECK_EVENTS 0x100
#define VOCTRL_RESET 0x101
struct vo_ohcodec_drain_req { int result; int platform_error; int reason; };
struct vo_ohcodec_surface_req { int invalid; int mark_invalid; };

/* -------------------------------------------------- exact source slices */
#define mapper_uninit vk_mapper_uninit
#include "actual-vk.inc"
#undef mapper_uninit
#include "actual-generic.inc"
#include "actual-gpu.inc"
#include "actual-registry.inc"
#include "actual-dispatch.inc"
#include "actual-vo.inc"
#include "actual-vd.inc"
#include "actual-vo_gpu_next.inc"
#include "actual-player_video.inc"
#include "actual-player_main.inc"

static void test_uninit(struct vo *vo)
{
    atomic_fetch_add(&c_uninit_begin, 1);
    event("EVENT uninit-begin");
    uninit(vo);
    destroy_event("uninit-end", &c_uninit_end);
}

static int real_driver_control(struct vo *vo, uint32_t request, void *data)
{
    (void)vo;
    struct priv *p = vo->priv;
    switch (request) {
#include "actual-gpu_control.inc"
    default:
        return -1;
    }
}

/* ------------------------------------------------------------- helpers */
static void fake_driver_uninit(struct ra_hwdec *hw)
{
    struct ohcodec_priv *p = hw->priv;
    hwdec_devices_remove(hw->devs, &p->hwctx);
    av_buffer_unref(&p->hwctx.av_device_ref);
    if (p->interop && p->interop->owner_uninit)
        p->interop->owner_uninit(hw);
    atomic_fetch_add(&c_owner_uninit, 1);
}
static void fake_owner_uninit_count(struct ra_hwdec *hw)
{
    (void)hw;
    atomic_fetch_add(&c_owner_uninit, 1);
}

static VkResult fake_signal_release(void *queue, uint32_t n, VkSemaphore *sem,
                                    VkImage image, int *fence_fd)
{
    (void)queue; (void)n; (void)sem; (void)image;
    if (fence_fd) *fence_fd = 42;
    return VK_SUCCESS;
}
static int platform_wait_result;
static atomic_int platform_wait_calls;
static VkResult fake_wait_idle(void *queue) {
    (void)queue; atomic_fetch_add(&platform_wait_calls, 1);
    printf("EVENT platform-wait rc=%d\n", platform_wait_result); fflush(stdout);
    return platform_wait_result;
}
static void fake_lock_queue(struct pl_vulkan *vk, uint32_t qf, uint32_t i)
{
    (void)vk; (void)qf; (void)i;
}
static void fake_unlock_queue(struct pl_vulkan *vk, uint32_t qf, uint32_t i)
{
    (void)vk; (void)qf; (void)i;
}

static void make_vk(struct ra_hwdec_mapper *mapper, struct ohcodec_mapper_priv *mp,
                    struct vk_mapper **out_v)
{
    struct vk_mapper *v = calloc(1, sizeof(*v));
    struct pl_vulkan *vk = calloc(1, sizeof(*vk));
    struct vk_import *e = calloc(1, sizeof(*e));
    vk->device = (VkDevice)1;
    vk->lock_queue = fake_lock_queue;
    vk->unlock_queue = fake_unlock_queue;
    v->vk = vk;
    v->gpu = (pl_gpu)1;
    v->signal_release = fake_signal_release;
    v->wait_idle = fake_wait_idle;
    v->queue = (void *)1;
    v->qf = 0;
    v->current = e;
    v->imports = NULL;
    v->num_imports = 1;
    v->window_buffer = (OHNativeWindowBuffer *)(uintptr_t)0x100;
    e->busy = true;
    e->seq = 7;
    e->image = 1;
    mp->priv = v;
    mapper->priv = mp;
    if (out_v) *out_v = v;
}

/* --------------------------------------------------------------- setup */
struct test_ctx {
    struct vo vo;
    struct priv p;
    struct vo_internal in;
    struct vo_driver driver;
    struct mp_dispatch_queue *dispatch;
    struct ra_hwdec *owner;
    struct ohcodec_priv owner_priv;
    struct ra_hwdec_mapper mapper;
    struct ohcodec_mapper_priv mapper_priv;
    struct ohcodec_interop interop;
    struct ohcodec_surface surface;
    struct ra_hwdec_mapper_driver mapper_driver;
    struct ra_hwdec_driver owner_driver;
    struct gl_next_opts next_opts;
    struct mp_filter vd;
    struct vd_ffmpeg_ctx vdctx;
    AVCodecContext *avctx;
    struct MPContext mpctx;
};

static struct test_ctx *g;

static void setup_ctx(struct test_ctx *t, bool with_decoder, bool with_mapper)
{
    memset(t, 0, sizeof(*t));
    g = t;

    t->driver.name = "gpu-next";
    t->driver.preinit = fake_preinit;
    t->driver.control = real_driver_control;
    t->driver.uninit = test_uninit;
    t->in.dispatch = mp_dispatch_create(NULL);
    t->in.stats = calloc(1, sizeof(struct stats_ctx));
    t->in.display_fps = 60.0;
    t->in.dr_helper = calloc(1, sizeof(struct dr_helper));
    t->in.current_frame = calloc(1, sizeof(struct vo_frame));
    t->in.frame_queued = calloc(1, sizeof(struct vo_frame));
    t->in.hasframe = true;
    t->in.hasframe_rendered = true;
    mp_mutex_init(&t->in.lock);
    mp_cond_init(&t->in.wakeup);
    t->vo.in = &t->in;
    t->vo.driver = &t->driver;
    t->vo.priv = &t->p;
    t->vo.log = calloc(1, sizeof(struct mp_log));
    t->vo.global = calloc(1, sizeof(struct mpv_global));
    t->vo.opts_cache = calloc(1, sizeof(struct m_config_cache));
    mp_mutex_init(&t->vo.params_mutex);
    t->p.log = t->vo.log;
    t->p.global = t->vo.global;
    t->p.gpu = (pl_gpu)1;
    t->p.pllog = (pl_log)1;
    t->p.queue = (pl_queue)calloc(1, sizeof(pl_queue));
    t->p.context = calloc(1, sizeof(struct gpu_ctx));
    t->p.next_opts = &t->next_opts;
    t->p.osd_state.entries[0].tex = (pl_tex)1;
    t->p.sub_tex = NULL;
    t->p.num_sub_tex = 0;
    t->p.user_hooks = NULL;
    t->p.num_user_hooks = 0;
    t->p.num_dr_buffers = 0;
    t->p.icc_profile = (pl_icc_object)1;
    t->p.rr = (pl_renderer)1;
    t->p.pars = (pl_options)1;
    t->p.perf_fresh.info[0].shader = (pl_shader_info *)1;
    t->p.perf_redraw.info[0].shader = (pl_shader_info *)1;
    t->p.dr_lock = (mp_mutex){0};
    mp_mutex_init(&t->p.dr_lock);

    t->owner_driver.name = "ohcodec";
    t->owner_driver.priv_size = sizeof(struct ohcodec_priv);
    t->owner_driver.imgfmts[0] = IMGFMT_OHCODEC;
    t->owner_driver.device_type = AV_HWDEVICE_TYPE_OHCODEC;
    t->owner_driver.uninit = fake_driver_uninit;
    t->owner = calloc(1, sizeof(struct ra_hwdec));
    t->owner->driver = &t->owner_driver;
    t->owner->priv = &t->owner_priv;
    t->owner->log = t->vo.log;
    t->owner_priv.interop = &t->interop;
    t->owner_priv.surface = &t->surface;

    t->interop.drain = ohcodec_drain;
    t->interop.owner_uninit = fake_owner_uninit_count;
    t->interop.mapper_uninit = fake_pl_uninit;

    if (with_mapper) {
        t->mapper.owner = t->owner;
        t->mapper.log = t->vo.log;
        t->mapper.driver = &t->mapper_driver;
        t->mapper.priv = &t->mapper_priv;
        t->mapper_driver.uninit = mapper_uninit;
        t->mapper_priv.last_token = (AVOHCodecBuffer *)(uintptr_t)0x200;
        t->mapper_priv.last_src = calloc(1, sizeof(struct mp_image));
        make_vk(&t->mapper, &t->mapper_priv, NULL);
        t->p.hwdec_mapper = &t->mapper;
        observed_mapper = &t->mapper;
    }
    observed_owner = t->owner;
    observed_vo = &t->vo;
    t->mpctx.video_out = &t->vo;
    t->mpctx.global = t->vo.global;
    t->mpctx.clients = calloc(1, sizeof(struct mp_client_api));
    t->mpctx.osd = calloc(1, sizeof(struct osd_state));
    t->mpctx.input = calloc(1, sizeof(struct input_ctx));
    t->mpctx.clipboard = calloc(1, sizeof(struct clipboard_ctx));
    t->mpctx.encode_lavc_ctx = calloc(1, sizeof(struct encode_lavc_context));
    t->mpctx.ipc_ctx = calloc(1, sizeof(struct mp_ipc_ctx));
    t->mpctx.mconfig = calloc(1, sizeof(struct m_config));
    t->mpctx.abort_list = calloc(1, sizeof(struct mp_abort_list));
    t->mpctx.num_abort_list = 0;
    mp_mutex_init(&t->mpctx.abort_lock);
    observed_mpctx = &t->mpctx;
    observed_mconfig = t->mpctx.mconfig;
    observed_abort_list = t->mpctx.abort_list;

    t->p.hwdec_ctx.log = t->vo.log;
    t->p.hwdec_ctx.global = t->vo.global;
    t->p.hwdec_ctx.ra_ctx = (struct ra_ctx *)1;
    t->p.hwdec_ctx.num_hwdecs = 1;
    t->p.hwdec_ctx.hwdecs = calloc(1, sizeof(struct ra_hwdec *));
    t->p.hwdec_ctx.hwdecs[0] = t->owner;
    observed_hwdecs = t->p.hwdec_ctx.hwdecs;

    t->vo.hwdec_devs = hwdec_devices_create();
    observed_devs = t->vo.hwdec_devs;
    t->owner->devs = t->vo.hwdec_devs;
    hwdec_devices_set_loader(t->vo.hwdec_devs, NULL, NULL);
    hwdec_devices_add(t->vo.hwdec_devs, &t->owner_priv.hwctx);
    atomic_fetch_add(&c_registry_add, 1);

    if (with_decoder) {
        t->avctx = calloc(1, sizeof(AVCodecContext));
        t->vdctx.avctx = t->avctx;
        t->vdctx.use_hwdec = true;
        t->vdctx.vo = &t->vo;
        t->vdctx.hwdec.lavc_device = AV_HWDEVICE_TYPE_OHCODEC;
        t->vd.priv = &t->vdctx;
        t->vo.hwdec_devs = t->vo.hwdec_devs;
    }
}

static void *observer_thread(void *arg)
{
    (void)arg;
    for (int i = 0; i < 25; i++) {
        event("EVENT observer-snapshot destroy_events=%d queue_destroy=%d "
              "registry_destroy=%d gpu_ctx_destroy=%d renderer_destroy=%d "
              "parent_vo_free=%d uninit_end=%d",
              atomic_load(&c_destroy_events), atomic_load(&c_queue_destroy),
              atomic_load(&c_registry_destroy), atomic_load(&c_gpu_ctx_destroy),
              atomic_load(&c_renderer_destroy), atomic_load(&c_parent_vo_free),
              atomic_load(&c_uninit_end));
        struct timespec ts = { .tv_sec = 0, .tv_nsec = 100000000 };
        nanosleep(&ts, NULL);
    }
    return NULL;
}

static void print_counts(void)
{
    event("EVENT counts queue_destroy=%d queue_reset=%d gpu_ctx_destroy=%d "
          "registry_destroy=%d dr_helper_free=%d parent_vo_free=%d "
          "parent_other_free=%d mapper_free=%d owner_free=%d owner_uninit=%d "
          "avctx_free=%d avctx_quarantine=%d barrier=%d uninit_begin=%d "
          "uninit_end=%d vo_destroy_end=%d",
          atomic_load(&c_queue_destroy), atomic_load(&c_queue_reset),
          atomic_load(&c_gpu_ctx_destroy), atomic_load(&c_registry_destroy),
          atomic_load(&c_dr_helper_free), atomic_load(&c_parent_vo_free),
          atomic_load(&c_parent_other_free), atomic_load(&c_mapper_free),
          atomic_load(&c_owner_free), atomic_load(&c_owner_uninit),
          atomic_load(&c_avctx_free), atomic_load(&c_avctx_quarantine),
          atomic_load(&c_barrier), atomic_load(&c_uninit_begin),
          atomic_load(&c_uninit_end), atomic_load(&c_vo_destroy_end));
    event("EVENT parent_counts mpctx_free=%d mconfig_free=%d abort_list_free=%d "
          "osd_free=%d input_free=%d clipboard_free=%d global_free=%d "
          "clients_free=%d command_free=%d encoder_free=%d ipc_free=%d "
          "audio_out_free=%d video_chain_uninit=%d msg_uninit=%d",
          atomic_load(&c_mpctx_free), atomic_load(&c_mconfig_free),
          atomic_load(&c_abort_list_free), atomic_load(&c_osd_free),
          atomic_load(&c_input_free), atomic_load(&c_clipboard_free),
          atomic_load(&c_global_free), atomic_load(&c_clients_free),
          atomic_load(&c_command_free), atomic_load(&c_encoder_free),
          atomic_load(&c_ipc_free), atomic_load(&c_audio_out_free),
          atomic_load(&c_video_chain_uninit), atomic_load(&c_msg_uninit));
    event("EVENT destroy_counts destroy_events=%d texture=%d renderer=%d "
          "options=%d cache=%d icc=%d lut=%d shader=%d vk_mapper=%d",
          atomic_load(&c_destroy_events), atomic_load(&c_texture_destroy),
          atomic_load(&c_renderer_destroy), atomic_load(&c_options_destroy),
          atomic_load(&c_cache_destroy), atomic_load(&c_icc_destroy),
          atomic_load(&c_lut_destroy), atomic_load(&c_shader_destroy),
          atomic_load(&c_vk_mapper_free));
}

static void *core_preflight(void *arg)
{
    struct test_ctx *t = arg;
    event("EVENT core-begin");
    uninit_avctx(&t->vd);
    event("EVENT core-after-avctx");
    mp_destroy(&t->mpctx);
    atomic_fetch_add(&c_vo_destroy_end, 1); event("EVENT core-after-mp-destroy");
    event("EVENT core-end");
    print_counts();
    return NULL;
}

static void *core_late(void *arg)
{
    struct test_ctx *t = arg;
    event("EVENT core-begin");
    mp_destroy(&t->mpctx);
    atomic_fetch_add(&c_vo_destroy_end, 1); event("EVENT core-after-mp-destroy");
    event("EVENT core-end");
    print_counts();
    return NULL;
}

static int start_vo_thread(struct test_ctx *t)
{
    return pthread_create(&t->in.thread, NULL, vo_thread, &t->vo);
}

static void join_vo_thread(struct test_ctx *t)
{
    pthread_join(t->in.thread, NULL);
}

static void run_case(const char *mode)
{
    bool decoder = !strncmp(mode, "preflight", 9) || !strcmp(mode, "normal") ||
                   !strcmp(mode, "release-error") || !strcmp(mode, "experiment");
    bool with_mapper = strcmp(mode, "normal-no-mapper") != 0;
    struct test_ctx t;
    setup_ctx(&t, decoder, with_mapper);

    if (!strcmp(mode, "normal-no-mapper")) {
        /* GL/software path: no OHCodec mapper, no drain, ordinary cleanup. */
        t.p.hwdec_mapper = NULL;
        t.p.hwdec_ctx.num_hwdecs = 0;
        hwdec_devices_remove(t.vo.hwdec_devs, &t.owner_priv.hwctx);
    }

    platform_wait_result = strstr(mode, "unsafe") ? -4 : 0;
    release_result = strstr(mode, "release-error") ? -1234 : 0;
    if (!strcmp(mode, "owner-retained-no-mapper")) {
        t.p.hwdec_mapper = NULL;
        t.owner->resource_retained = true;
        t.owner_priv.surface_invalid = true;
        event("EVENT setup-owner-retained-without-mapper");
    }

    if (start_vo_thread(&t) != 0) {
        perror("pthread_create");
        exit(2);
    }

    pthread_t core;
    void *(*fn)(void *) = decoder ? core_preflight : core_late;
    if (pthread_create(&core, NULL, fn, &t) != 0) {
        perror("pthread_create core");
        exit(2);
    }
    if (strstr(mode, "unsafe") || !strcmp(mode, "experiment")) {
        pthread_t observer;
        if (pthread_create(&observer, NULL, observer_thread, NULL) == 0)
            pthread_detach(observer);
    }

    /* Observe for a bounded interval.  This is not the acceptance criterion:
     * the external runner also requires the P28_TERMINAL barrier line and the
     * absence of every destruction event.  A normal path completes and prints
     * counts; a barrier/unknown hang stays alive for the runner to inspect. */
    for (int i = 0; i < 20; i++) {
        if (atomic_load(&c_vo_destroy_end)) {
            event("EVENT cleanup-complete");
            break;
        }
        struct timespec ts = { .tv_sec = 0, .tv_nsec = 100000000 };
        nanosleep(&ts, NULL);
    }

    if (atomic_load(&c_vo_destroy_end)) {
        event("EVENT all-done");
    } else {
        event("EVENT blocked-no-cleanup");
        for (;;)
            sleep(1);
    }
}

static int mode_callback_retained(void)
{
    struct ohcodec_surface surface = {0};
    mp_mutex_init(&surface.lock);
    mp_cond_init(&surface.cond);
    on_frame_available(&surface);
    on_frame_available(&surface);
    bool pass = surface.pending == 2;
    printf("%s callback-retained pending=%u\n", pass ? "PASS" : "FAIL",
           surface.pending);
    return pass ? 0 : 1;
}

static void *callback_worker(void *opaque) {
    for (int i=0; i<1000; i++) on_frame_available(opaque);
    return NULL;
}
static int normal_state_probes(void) {
    struct test_ctx t; setup_ctx(&t, false, true);
    platform_wait_result=-4;
    int e1=0,e2=0;
    int r1=ohcodec_mapper_drain(&t.mapper, OHCODEC_DRAIN_REASON_CLOSE, &e1);
    int r2=ohcodec_mapper_drain(&t.mapper, OHCODEC_DRAIN_REASON_CLOSE, &e2);
    mp_mutex_init(&t.surface.lock);mp_cond_init(&t.surface.cond);
    pthread_t a,b;
    pthread_create(&a,NULL,callback_worker,&t.surface);
    pthread_create(&b,NULL,callback_worker,&t.surface);
    pthread_join(a,NULL);pthread_join(b,NULL);
    bool ok=r1==OHCODEC_DRAIN_UNSAFE && r2==r1 && e1==-4 && e2==e1 &&
      atomic_load(&platform_wait_calls)==1 && t.mapper.resource_retained &&
      t.owner->resource_retained && t.owner_priv.surface_invalid && t.surface.pending==2000;
    printf("%s normal-state-probes r1=%d r2=%d calls=%d pending=%u\n",ok?"PASS":"FAIL",r1,r2,atomic_load(&platform_wait_calls),t.surface.pending);
    return ok?0:1;
}
int main(int argc, char **argv)
{
    if (argc != 2)
        return 64;
    if (!strcmp(argv[1], "normal-state-probes")) return normal_state_probes();
    if (!strcmp(argv[1], "selftest"))
        return 0;
    if (!strcmp(argv[1], "callback-retained"))
        return mode_callback_retained();
    if (!strcmp(argv[1], "relaxed-mutant")) {
        relaxed_assert = 1;
        run_case("preflight-unsafe");
    } else {
        run_case(argv[1]);
    }
    return 0;
}
