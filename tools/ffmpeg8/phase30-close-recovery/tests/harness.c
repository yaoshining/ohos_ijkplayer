/*
 * T008 real-function harness: OHCodec decoder callback/token/Close lifetime.
 *
 * The actual ohdec.c function bodies are extracted verbatim. FFmpeg/libavutil
 * primitives (AVBufferRef refcounts, pthread mutex/cond, FIFO) and HarmonyOS
 * platform APIs are stubs with controllable blocking and event recording.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <setjmp.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>
#include <stdatomic.h>

/* ---------------------------------------------------------------- events */
enum {
    EV_CREATE = 1, EV_CONFIGURE, EV_SURFACE, EV_REGISTER, EV_PREPARE, EV_START,
    EV_STOP, EV_DESTROY, EV_FLUSH, EV_RENDER_BEGIN, EV_RENDER_END,
    EV_FREE_BUF, EV_PUSH_INPUT, EV_CALLBACK_ENTER, EV_CALLBACK_EXIT,
};
static const char *ev_name(int e) {
    switch (e) {
    case EV_CREATE: return "create";
    case EV_CONFIGURE: return "configure";
    case EV_SURFACE: return "set_surface";
    case EV_REGISTER: return "register_callback";
    case EV_PREPARE: return "prepare";
    case EV_START: return "start";
    case EV_STOP: return "stop";
    case EV_DESTROY: return "destroy";
    case EV_FLUSH: return "flush";
    case EV_RENDER_BEGIN: return "render_begin";
    case EV_RENDER_END: return "render_end";
    case EV_FREE_BUF: return "free_buffer";
    case EV_PUSH_INPUT: return "push_input";
    case EV_CALLBACK_ENTER: return "callback_enter";
    case EV_CALLBACK_EXIT: return "callback_exit";
    default: return "?";
    }
}
static int events[512], nevents;
static int mutex_destroy_calls, cond_destroy_calls;
static void ev(int e) { if (nevents < (int)(sizeof(events)/sizeof(events[0]))) events[nevents++] = e; }
static int first_ev(int e) { for (int i = 0; i < nevents; i++) if (events[i] == e) return i; return -1; }
static int count_ev(int e) { int n = 0; for (int i = 0; i < nevents; i++) n += events[i] == e; return n; }
static void dump_events(void) {
    for (int i = 0; i < nevents; i++) printf("%s%s", i ? "," : "", ev_name(events[i]));
    printf("\n");
}

/* ------------------------------------------------------------- FFmpeg */
#define AVERROR(e) (-(e))
#define AVERROR_BUG (-100)
#define AVERROR_EXTERNAL (-101)
#define AVERROR_ENOMEM (-12)
#define AVERROR_EAGAIN (-11)
#define AVERROR_EOF (-541478725)
#define AVERROR_EALREADY (-114)
#define AVERROR_ESTALE (-116)
#define AVERROR_EINVAL (-22)
#define AV_NOPTS_VALUE INT64_MIN
#define AV_TIME_BASE 1000000
#define AV_PIX_FMT_NONE (-1)
#define AV_PIX_FMT_OHCODEC 200
#define AV_PIX_FMT_NV12 23
#define AV_PIX_FMT_P010 2000
#define AV_CODEC_ID_H264 27
#define AV_CODEC_ID_HEVC 173
#define AV_PROFILE_HEVC_MAIN_10 2
#define AV_PROFILE_H264_HIGH_10 110
#define AV_HWDEVICE_TYPE_OHCODEC 100
#define AV_ERR_OK 0
#define AV_ERR_UNKNOWN 1
#define AV_ERR_NO_MEMORY 2
#define AV_ERR_INVALID_VAL 3
#define AV_ERR_OPERATE_NOT_PERMIT 4
#define NATIVEBUFFER_PIXEL_FMT_YCBCR_P010 10
#define NATIVEBUFFER_PIXEL_FMT_YCRCB_P010 11
#define AVCODEC_BUFFER_FLAGS_EOS 1
#define AVCODEC_BUFFER_FLAGS_SYNC_FRAME 2
#define HARDWARE 1
#define SOFTWARE 2
#define av_cold
#define FFMIN(a,b) ((a) < (b) ? (a) : (b))
#define AV_TIME_BASE_Q ((AVRational){1, AV_TIME_BASE})
#define AV_PKT_FLAG_KEY 1
#ifndef MAP_ANON
#ifdef __APPLE__
#define MAP_ANON 0x1000
#else
#define MAP_ANON 0x20 /* Linux MAP_ANONYMOUS, visible without _DEFAULT_SOURCE */
#endif
#endif
#define OH_MD_KEY_WIDTH "width"
#define OH_MD_KEY_HEIGHT "height"
#define AV_PIXEL_FORMAT_NV12 23
#define AV_PIXEL_FORMAT_SURFACE_FORMAT 99
typedef void OHNativeWindow;
static const char *av_hwdevice_get_type_name(int type){(void)type;return "ohcodec";}
#define OH_MD_KEY_VIDEO_PIC_WIDTH "video_pic_width"
#define OH_MD_KEY_VIDEO_PIC_HEIGHT "video_pic_height"
#define OH_MD_KEY_VIDEO_STRIDE "video_stride"
#define OH_MD_KEY_VIDEO_SLICE_HEIGHT "video_slice_height"
#define OH_MD_KEY_BITS_PER_CODED_SAMPLE "bits_per_coded_sample"
#define OH_MD_KEY_PIXEL_FORMAT "pixel_format"
#define OH_MD_KEY_MATRIX_COEFFICIENTS "matrix_coefficients"
#define OH_MD_KEY_COLOR_PRIMARIES "color_primaries"
#define OH_MD_KEY_TRANSFER_CHARACTERISTICS "transfer_characteristics"
#define OH_MD_KEY_RANGE_FLAG "range_flag"
#define OH_MD_KEY_VIDEO_SAR "video_sar"
#define AVCOL_RANGE_JPEG 2
#define AVCOL_RANGE_MPEG 1

typedef struct AVBuffer {
    atomic_int refcount;
    uint8_t *data;
    int size;
    void (*free)(void *opaque, uint8_t *data);
    void *opaque;
} AVBuffer;
typedef struct AVBufferRef { AVBuffer *buffer; uint8_t *data; int size; } AVBufferRef;

static AVBufferRef *av_buffer_create(uint8_t *data, int size,
                                     void (*free_fn)(void *, uint8_t *),
                                     void *opaque, int flags) {
    (void)flags;
    AVBuffer *b = calloc(1, sizeof(*b));
    AVBufferRef *r = calloc(1, sizeof(*r));
    if (!b || !r) { free(b); free(r); return NULL; }
    atomic_init(&b->refcount, 1);
    b->data = data; b->size = size; b->free = free_fn; b->opaque = opaque;
    r->buffer = b; r->data = data; r->size = size;
    return r;
}
static AVBufferRef *av_buffer_ref(AVBufferRef *r) {
    if (!r) return NULL;
    atomic_fetch_add_explicit(&r->buffer->refcount, 1, memory_order_acq_rel);
    AVBufferRef *n = calloc(1, sizeof(*n));
    if (!n) {
        atomic_fetch_sub_explicit(&r->buffer->refcount, 1, memory_order_acq_rel);
        return NULL;
    }
    *n = *r;
    return n;
}
static void av_buffer_unref(AVBufferRef **rp) {
    AVBufferRef *r = *rp;
    if (!r) return;
    *rp = NULL;
    if (atomic_fetch_sub_explicit(&r->buffer->refcount, 1, memory_order_acq_rel) == 1) {
        AVBuffer *b = r->buffer;
        if (b->free) b->free(b->opaque, b->data);
        free(b);
    }
    free(r);
}
static void *av_mallocz(size_t n) { return calloc(1, n); }
static void av_free(void *p) { free(p); }
static int diagnostic_challenges;
static void av_log(void *ctx, int level, const char *fmt, ...) {
    if (strstr(fmt,"op=admission-challenge")) diagnostic_challenges++;
    (void)ctx; (void)level;
    if (!getenv("OHDEC_TEST_VERBOSE")) return;
    va_list ap; va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
}
#define AV_LOG_INFO 1
#define AV_LOG_DEBUG 2
#define AV_LOG_ERROR 3
#define AV_LOG_WARNING 4
#define av_err2str(e) "err"

typedef struct AVMutex { pthread_mutex_t m; } AVMutex;
typedef struct AVCond { pthread_cond_t c; } AVCond;
static int ff_mutex_init(AVMutex *m, const void *a) { (void)a; return pthread_mutex_init(&m->m, NULL); }
static void ff_mutex_destroy(AVMutex *m) { mutex_destroy_calls++; pthread_mutex_destroy(&m->m); }
static pthread_mutex_t block_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t block_cond = PTHREAD_COND_INITIALIZER;
static int render_block, render_entered, render_release;
static AVMutex *watch_mutex;
static int watch_waiters;
static void ff_mutex_lock(AVMutex *m) {
    if (m == watch_mutex) {
        pthread_mutex_lock(&block_lock);
        watch_waiters++;
        pthread_cond_broadcast(&block_cond);
        pthread_mutex_unlock(&block_lock);
    }
    pthread_mutex_lock(&m->m);
}
static void ff_mutex_unlock(AVMutex *m) { pthread_mutex_unlock(&m->m); }
static int ff_cond_init(AVCond *c, const void *a) { (void)a; return pthread_cond_init(&c->c, NULL); }
static void ff_cond_destroy(AVCond *c) { cond_destroy_calls++; pthread_cond_destroy(&c->c); }
static void ff_cond_signal(AVCond *c) { pthread_cond_signal(&c->c); }
static void ff_cond_broadcast(AVCond *c) { pthread_cond_broadcast(&c->c); }
static int ff_cond_timedwait(AVCond *c, AVMutex *m, const struct timespec *ts) {
    return pthread_cond_timedwait(&c->c, &m->m, ts);
}
static int ff_cond_wait(AVCond *c, AVMutex *m) { return pthread_cond_wait(&c->c, &m->m); }

typedef struct AVFifo { int count; } AVFifo;
static AVFifo *av_fifo_alloc2(size_t n, size_t elem, int flags) {
    (void)n; (void)elem; (void)flags; return calloc(1, sizeof(AVFifo));
}
static void av_fifo_freep2(AVFifo **f) { free(*f); *f = NULL; }
static void av_fifo_reset2(AVFifo *f) { if (f) f->count = 0; }
static int av_fifo_write(AVFifo *f, const void *p, size_t n) { (void)p; if (!f) return AVERROR_EINVAL; f->count += (int)n; return 0; }
static int av_fifo_read(AVFifo *f, void *p, size_t n) { (void)f; (void)p; (void)n; return AVERROR_EAGAIN; }

typedef struct AVPacket { uint8_t *data; int size; int flags; int64_t pts; } AVPacket;
static void av_packet_unref(AVPacket *p) { if (p) { p->data = NULL; p->size = 0; p->flags = 0; p->pts = 0; } }
typedef struct AVRational { int num, den; } AVRational;
typedef struct AVFrame {
    int width, height, format;
    AVBufferRef *buf[8];
    AVBufferRef *hw_frames_ctx;
    uint8_t *data[8];
    int64_t pts, pkt_dts;
} AVFrame;
typedef struct AVDictionary AVDictionary;
typedef enum AVPixelFormat { AV_PIX_FMT_PLACEHOLDER = 0 } AVPixelFormat;
typedef enum AVCodecID { AV_CODEC_ID_PLACEHOLDER = 0 } AVCodecID;
typedef struct AVCodecContext {
    enum AVCodecID codec_id;
    void *priv_data;
    int width, height;
    enum AVPixelFormat pix_fmt, sw_pix_fmt;
    int profile;
    int bits_per_raw_sample;
    int colorspace, color_primaries, color_trc, color_range;
    AVBufferRef *hw_device_ctx;
    AVBufferRef *hw_frames_ctx;
    AVRational pkt_timebase;
    void *coded_side_data;
    int nb_coded_side_data;
} AVCodecContext;
typedef struct AVHWDeviceContext { int type; void *hwctx; } AVHWDeviceContext;
typedef struct AVOHCodecDeviceContext { void *native_window; } AVOHCodecDeviceContext;
typedef struct AVHWFramesContext { int format, sw_format, width, height; } AVHWFramesContext;

/* ------------------------------------------------------- HarmonyOS stubs */
typedef struct OH_AVCodec { int id; } OH_AVCodec;
typedef struct OH_AVBuffer { int index; uint8_t *addr; int capacity; } OH_AVBuffer;
typedef struct OH_AVFormat { int dummy; } OH_AVFormat;
typedef struct OH_AVCapability { int id; } OH_AVCapability;
typedef struct OH_AVCodecBufferAttr { int64_t pts; int size; int offset; uint32_t flags; } OH_AVCodecBufferAttr;
typedef int OH_AVErrCode;
typedef struct OH_AVCodecCallback {
    void (*onError)(OH_AVCodec *, int32_t, void *);
    void (*onStreamChanged)(OH_AVCodec *, OH_AVFormat *, void *);
    void (*onNeedInputBuffer)(OH_AVCodec *, uint32_t, OH_AVBuffer *, void *);
    void (*onNewOutputBuffer)(OH_AVCodec *, uint32_t, OH_AVBuffer *, void *);
} OH_AVCodecCallback;

typedef struct OHHdrState { int x; } OHHdrState;
typedef struct DOVIContext { void *logctx; } DOVIContext;
typedef struct H2645Packet { int nb_nals; } H2645Packet;
typedef struct H2645NAL { int type; int size; int raw_size; int nuh_layer_id; int temporal_id; uint8_t *raw_data; uint8_t *data; } H2645NAL;

static OH_AVCodecCallback g_cb;
static void *g_cb_userdata;
static OH_AVCodec *g_codec;
static int stop_result = AV_ERR_OK;
static int start_result = AV_ERR_OK;
static int prepare_result = AV_ERR_OK;
static int flush_result = AV_ERR_OK;
static int render_result = AV_ERR_OK;
static int destroy_result = AV_ERR_OK;
static int stop_calls, destroy_calls, render_calls, free_calls;

static OH_AVCodec *OH_VideoDecoder_CreateByName(const char *name) {
    (void)name; ev(EV_CREATE);
    g_codec = calloc(1, sizeof(*g_codec)); g_codec->id = 1; return g_codec;
}
static OH_AVErrCode OH_VideoDecoder_Destroy(OH_AVCodec *dec) {
    ev(EV_DESTROY); destroy_calls++;
    if (destroy_result == AV_ERR_OK) free(dec);
    return destroy_result;
}
static OH_AVErrCode OH_VideoDecoder_Configure(OH_AVCodec *dec, OH_AVFormat *fmt) {
    (void)dec; (void)fmt; ev(EV_CONFIGURE); return AV_ERR_OK;
}
static OH_AVErrCode OH_VideoDecoder_SetSurface(OH_AVCodec *dec, void *window) {
    (void)dec; (void)window; ev(EV_SURFACE); return AV_ERR_OK;
}
static OH_AVErrCode OH_VideoDecoder_RegisterCallback(OH_AVCodec *dec, OH_AVCodecCallback cb, void *userdata) {
    (void)dec; ev(EV_REGISTER); g_cb = cb; g_cb_userdata = userdata; return AV_ERR_OK;
}
static OH_AVErrCode OH_VideoDecoder_Prepare(OH_AVCodec *dec) { (void)dec; ev(EV_PREPARE); return prepare_result; }
static OH_AVErrCode OH_VideoDecoder_Start(OH_AVCodec *dec) { (void)dec; ev(EV_START); return start_result; }
static OH_AVErrCode OH_VideoDecoder_Stop(OH_AVCodec *dec) { (void)dec; ev(EV_STOP); stop_calls++; return stop_result; }
static OH_AVErrCode OH_VideoDecoder_Flush(OH_AVCodec *dec) { (void)dec; ev(EV_FLUSH); return flush_result; }

/* blocking render control for the token/Close race */
static OH_AVErrCode OH_VideoDecoder_RenderOutputBuffer(OH_AVCodec *dec, uint32_t index) {
    (void)dec; (void)index;
    ev(EV_RENDER_BEGIN); render_calls++;
    pthread_mutex_lock(&block_lock);
    render_entered = 1;
    pthread_cond_broadcast(&block_cond);
    while (render_block && !render_release)
        pthread_cond_wait(&block_cond, &block_lock);
    pthread_mutex_unlock(&block_lock);
    ev(EV_RENDER_END);
    return render_result;
}
static OH_AVErrCode OH_VideoDecoder_FreeOutputBuffer(OH_AVCodec *dec, uint32_t index) {
    (void)dec; (void)index; ev(EV_FREE_BUF); free_calls++; return AV_ERR_OK;
}
static OH_AVErrCode OH_VideoDecoder_PushInputBuffer(OH_AVCodec *dec, uint32_t index) {
    (void)dec; (void)index; ev(EV_PUSH_INPUT); return AV_ERR_OK;
}
static OH_AVFormat *OH_AVFormat_Create(void) { return calloc(1, sizeof(OH_AVFormat)); }
static void OH_AVFormat_Destroy(OH_AVFormat *f) { free(f); }
static void OH_AVFormat_SetIntValue(OH_AVFormat *f, const char *k, int32_t v) { (void)f; (void)k; (void)v; }
static bool OH_AVFormat_GetIntValue(OH_AVFormat *f, const char *k, int32_t *v) { (void)f; (void)k; (void)v; return false; }
static bool OH_AVFormat_GetDoubleValue(OH_AVFormat *f, const char *k, double *v) { (void)f; (void)k; (void)v; return false; }
static const char *OH_AVFormat_DumpInfo(OH_AVFormat *f) { (void)f; return "stub-format"; }
static OH_AVCapability *OH_AVCodec_GetCapabilityByCategory(const char *mime, bool encoder, int category) {
    (void)mime; (void)encoder; (void)category; static OH_AVCapability cap = {1}; return &cap;
}
static const char *OH_AVCapability_GetName(OH_AVCapability *cap) { (void)cap; return "fake.decoder"; }
static uint8_t *OH_AVBuffer_GetAddr(OH_AVBuffer *b) { return b ? b->addr : NULL; }
static int32_t OH_AVBuffer_GetCapacity(OH_AVBuffer *b) { return b ? b->capacity : 0; }
static OH_AVErrCode OH_AVBuffer_GetBufferAttr(OH_AVBuffer *b, OH_AVCodecBufferAttr *a) { (void)b; memset(a, 0, sizeof(*a)); return AV_ERR_OK; }
static OH_AVErrCode OH_AVBuffer_SetBufferAttr(OH_AVBuffer *b, const OH_AVCodecBufferAttr *a) { (void)b; (void)a; return AV_ERR_OK; }
static OH_AVFormat *OH_VideoDecoder_GetOutputDescription(OH_AVCodec *dec) { (void)dec; return OH_AVFormat_Create(); }

/* --------------------------------------------------------- ffmpeg helpers */
static int ff_oh_err_to_ff_err(OH_AVErrCode err) { return err == AV_ERR_OK ? 0 : AVERROR_EXTERNAL; }
static const char *ff_oh_mime(enum AVCodecID id, AVCodecContext *avctx) { (void)id; (void)avctx; return "video/avc"; }
static int ff_set_dimensions(AVCodecContext *avctx, int w, int h) { avctx->width = w; avctx->height = h; return 0; }
static void ff_set_sar(AVCodecContext *avctx, AVRational sar) { (void)avctx; (void)sar; }
static AVRational av_d2q(double d, int max) { (void)d; (void)max; return (AVRational){1,1}; }
static int64_t av_rescale_q(int64_t a, AVRational bq, AVRational cq) { (void)bq; (void)cq; return a; }
static int64_t p27_monotonic_us(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000 + ts.tv_nsec / 1000;
}
static enum AVPixelFormat ff_oh_pix_to_ff_pix(int fmt) { (void)fmt; return AV_PIX_FMT_NV12; }
static void ff_oh_hdr_reset(OHHdrState *h) { (void)h; }
static void ff_oh_hdr_finish(OHHdrState *h) { (void)h; }
static int ff_oh_hdr_prepare(OHHdrState *h, AVCodecContext *a, const uint8_t *d, int n, int64_t pts, uint64_t gen) {
    (void)h; (void)a; (void)d; (void)n; (void)pts; (void)gen; return 0;
}
static void ff_oh_hdr_commit(OHHdrState *h) { (void)h; }
static int ff_oh_hdr_attach(OHHdrState *h, AVCodecContext *a, AVFrame *f, uint64_t gen, int64_t pts) {
    (void)h; (void)a; (void)f; (void)gen; (void)pts; return 0;
}
static void ff_dovi_ctx_unref(DOVIContext *c) { (void)c; }
static void ff_dovi_ctx_flush(DOVIContext *c) { (void)c; }
static void ff_h2645_packet_uninit(H2645Packet *p) { (void)p; }
static int ff_h2645_packet_split(H2645Packet *p, const uint8_t *d, int n, AVCodecContext *a, int mode, int id, int flags) {
    (void)p; (void)d; (void)n; (void)a; (void)mode; (void)id; (void)flags; return 0;
}

/* ---------------------------------------------------- extracted structs */
typedef struct AVOHCodecBuffer AVOHCodecBuffer;
typedef struct OHCodecDecQueueItem {
    uint32_t index;
    OH_AVBuffer *buffer;
    uint64_t generation;
} OHCodecDecQueueItem;
typedef struct OHDoviFrame { int64_t pts; AVBufferRef *rpu; AVBufferRef *metadata; } OHDoviFrame;
typedef struct OHCodecDecRef {
    OH_AVCodec *dec;
    atomic_uint_fast64_t generation;
    uint64_t diagnostic_instance;
    uint64_t diagnostic_surface;
    bool diagnostic_claimed;
    /* Phase28 additions (ignored by baseline functions). */
    AVCodecContext *attached;
    AVMutex gate;
    AVCond gate_cond;
    int active;
    bool detached;
    bool paused;
    bool gate_initialized;
    bool start_attempted;
    bool stopped;
    bool destroyed;
} OHCodecDecRef;
typedef struct OHCodecDecContext {
    void *avclass;
    OH_AVCodec *dec;
    AVBufferRef *dec_ref;
    AVMutex input_mutex;
    AVCond input_cond;
    AVFifo *input_queue;
    AVMutex output_mutex;
    AVCond output_cond;
    AVFifo *output_queue;
    AVPacket pkt;
    OHHdrState hdr;
    DOVIContext dovi_ctx;
    H2645Packet dovi_pkt;
    OHDoviFrame dovi_frames[64];
    int nb_dovi_frames;
    int decode_status;
    bool eof_sent;
    atomic_bool accepting_callbacks;
    bool output_to_window;
    bool got_stream_info;
    int width, height, stride, slice_height;
    int pix_fmt;
    int bit_depth;
    char *name;
    int allow_sw;
    /* Phase28 additions (ignored by baseline functions). */
    bool locks_initialized;
    bool queues_initialized;
    bool platform_started;
} OHCodecDecContext;
struct AVOHCodecBuffer {
    uint32_t index;
    AVBufferRef *dec_ref;
    uint64_t generation;
    atomic_bool released;
};

static int oh_decode_init_hwframes(OHCodecDecContext *s, AVCodecContext *avctx, enum AVPixelFormat sw) {
    (void)s; (void)avctx; (void)sw; return 0;
}
static void oh_decode_clear_dovi(OHCodecDecContext *s) {
    for (int i = 0; i < s->nb_dovi_frames; i++) {
        av_buffer_unref(&s->dovi_frames[i].rpu);
        av_buffer_unref(&s->dovi_frames[i].metadata);
    }
    s->nb_dovi_frames = 0;
}

/* Phase28 terminal-failure globals referenced by the extracted functions. */
static atomic_bool ohcodec_terminal_failure = ATOMIC_VAR_INIT(false);
static atomic_int ohcodec_failed_destroy_count;

/* Actual production functions. */
static int OH_NativeWindow_GetSurfaceId(OHNativeWindow *window, uint64_t *surface) {
    *surface = (uint64_t)(uintptr_t)window; return 0;
}
#ifdef MP_OHCODEC_DIAGNOSTIC
#include "ohcodec_diagnostic.h"
#endif
#include "actual-ohdec.inc"

/* ------------------------------------------------------------ test utils */
struct env {
    AVCodecContext avctx;
    OHCodecDecContext *s;
    AVOHCodecBuffer *token;
};

static bool test_same_consumer;
static AVOHCodecDeviceContext shared_device={.native_window=(void *)0x555};
static AVHWDeviceContext shared_ctx={.type=AV_HWDEVICE_TYPE_OHCODEC,.hwctx=&shared_device};
static AVBufferRef shared_ref={.data=(uint8_t *)&shared_ctx};
static int env_start(struct env *e, bool with_token) {
    memset(e, 0, sizeof(*e));
    e->s = calloc(1, sizeof(*e->s));
    e->avctx.priv_data = e->s;
    e->avctx.codec_id = AV_CODEC_ID_H264;
    e->avctx.width = 1920;
    e->avctx.height = 1080;
    e->avctx.pkt_timebase = (AVRational){1, 1000};
    e->s->name = strdup("fake.decoder");
    ff_mutex_init(&e->s->input_mutex, NULL);
    ff_cond_init(&e->s->input_cond, NULL);
    ff_mutex_init(&e->s->output_mutex, NULL);
    ff_cond_init(&e->s->output_cond, NULL);
    e->s->input_queue = av_fifo_alloc2(16, sizeof(OHCodecDecQueueItem), 0);
    e->s->output_queue = av_fifo_alloc2(16, sizeof(OHCodecDecQueueItem), 0);
    atomic_init(&e->s->accepting_callbacks, false);
    e->s->locks_initialized = true;
    e->s->queues_initialized = true;
    if (oh_decode_create(e->s, &e->avctx) < 0)
        return -1;
    if(test_same_consumer){ e->avctx.hw_device_ctx=&shared_ref; if(oh_decode_set_format(e->s,&e->avctx)<0)return -1; }
    if (oh_decode_start(e->s, &e->avctx) < 0)
        return -1;
    if (with_token) {
        e->token = calloc(1, sizeof(*e->token));
        e->token->dec_ref = av_buffer_ref(e->s->dec_ref);
        e->token->index = 3;
        e->token->generation = oh_decode_generation(e->s);
        atomic_init(&e->token->released, false);
    }
    return 0;
}

static void env_release_token(struct env *e) {
    if (e->token) {
        av_buffer_unref(&e->token->dec_ref);
        free(e->token);
        e->token = NULL;
    }
}

/* ------------------------------------------------------------ test modes */
static int mode_close_held_frame(void) {
    struct env e;
    if (env_start(&e, true) < 0) return 70;
    oh_decode_close(&e.avctx);
    dump_events();
    int stops = count_ev(EV_STOP), destroys = count_ev(EV_DESTROY);
    int stop_at = first_ev(EV_STOP), destroy_at = first_ev(EV_DESTROY);
    bool ok = stops == 1 && destroys == 1 && stop_at >= 0 && destroy_at > stop_at;
    if (!ok) {
        printf("FAIL close-held-frame: close returned with stops=%d destroys=%d "
               "(stop_at=%d destroy_at=%d); expected Stop and Destroy inside Close\n",
               stops, destroys, stop_at, destroy_at);
        env_release_token(&e);
        return 1;
    }
    env_release_token(&e);
    int destroys_after = count_ev(EV_DESTROY);
    if (destroys_after != 1) {
        printf("FAIL close-held-frame: late token release destroyed decoder again (%d)\n",
               destroys_after);
        return 1;
    }
    printf("PASS close-held-frame\n");
    return 0;
}

/* Controlled SIGSEGV to prove a callback dereferenced a detached context. */
static sigjmp_buf segv_jmp;
static volatile sig_atomic_t segv_hit;
static void segv_handler(int sig) { (void)sig; segv_hit = 1; siglongjmp(segv_jmp, 1); }

static int mode_callback_after_close(void) {
    struct env e;
    if (env_start(&e, true) < 0) return 70;
    OH_AVCodecCallback cb = g_cb;
    void *userdata = g_cb_userdata;
    OH_AVCodec *dec = g_codec;
    oh_decode_close(&e.avctx);
    /* Detach and poison the old context behind the platform callback. */
    free(e.s);
    e.s = NULL;
    void *bad = mmap(NULL, 4096, PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0);
    if (bad == MAP_FAILED) return 71;
    e.avctx.priv_data = bad;

    struct sigaction sa = {0}, old;
    sa.sa_handler = segv_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_NODEFER;
    sigaction(SIGSEGV, &sa, &old);
    sigaction(SIGBUS, &sa, &old);
    segv_hit = 0;
    OH_AVBuffer *buf = calloc(1, sizeof(*buf));
    if (sigsetjmp(segv_jmp, 1) == 0) {
        if (cb.onNeedInputBuffer) cb.onNeedInputBuffer(dec, 0, buf, userdata);
        if (cb.onNewOutputBuffer) cb.onNewOutputBuffer(dec, 0, buf, userdata);
        if (cb.onError) cb.onError(dec, AV_ERR_UNKNOWN, userdata);
        if (cb.onStreamChanged) cb.onStreamChanged(dec, OH_AVFormat_Create(), userdata);
    }
    sigaction(SIGSEGV, &old, NULL);
    sigaction(SIGBUS, &old, NULL);
    free(buf);
    munmap(bad, 4096);
    dump_events();
    if (segv_hit) {
        printf("FAIL callback-after-close: a platform callback dereferenced the "
               "detached AVCodecContext\n");
        env_release_token(&e);
        return 1;
    }
    printf("PASS callback-after-close\n");
    env_release_token(&e);
    return 0;
}

static void wait_flag(int *flag) {
    pthread_mutex_lock(&block_lock);
    while (!*flag) pthread_cond_wait(&block_cond, &block_lock);
    pthread_mutex_unlock(&block_lock);
}

static int timed_wait_flag(int *flag, int ms) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += ms / 1000;
    ts.tv_nsec += (long)(ms % 1000) * 1000000L;
    if (ts.tv_nsec >= 1000000000L) { ts.tv_sec++; ts.tv_nsec -= 1000000000L; }
    pthread_mutex_lock(&block_lock);
    int ret = 0;
    while (!*flag) {
        if (pthread_cond_timedwait(&block_cond, &block_lock, &ts) == ETIMEDOUT) { ret = -1; break; }
    }
    pthread_mutex_unlock(&block_lock);
    return ret;
}

static struct env race_env;
static int close_started, close_done;
static void *close_thread(void *arg) {
    (void)arg;
    __atomic_store_n(&close_started, 1, __ATOMIC_RELEASE);
    pthread_mutex_lock(&block_lock); pthread_cond_broadcast(&block_cond); pthread_mutex_unlock(&block_lock);
    oh_decode_close(&race_env.avctx);
    __atomic_store_n(&close_done, 1, __ATOMIC_RELEASE);
    pthread_mutex_lock(&block_lock); pthread_cond_broadcast(&block_cond); pthread_mutex_unlock(&block_lock);
    return NULL;
}

static void *render_thread(void *arg) {
    (void)arg;
    av_ohcodec_release_buffer(race_env.token, 1);
    return NULL;
}

static int mode_token_close_race(void) {
    if (env_start(&race_env, true) < 0) return 70;
    render_block = 1; render_entered = 0; render_release = 0;
    stop_calls = 0; close_started = 0; close_done = 0;
    pthread_t rt, ct;
    pthread_create(&rt, NULL, render_thread, NULL);
    if (timed_wait_flag(&render_entered, 1000) != 0) {
        printf("FAIL token-close-race: render did not enter\n");
        return 1;
    }
    pthread_create(&ct, NULL, close_thread, NULL);
    if (timed_wait_flag(&close_started, 1000) != 0) {
        printf("FAIL token-close-race: close did not start\n");
        return 1;
    }
    int stopped_early = timed_wait_flag(&close_done, 120) == 0 || stop_calls > 0;
    /* release the in-flight platform render */
    pthread_mutex_lock(&block_lock);
    render_release = 1;
    pthread_cond_broadcast(&block_cond);
    pthread_mutex_unlock(&block_lock);
    pthread_join(rt, NULL);
    pthread_join(ct, NULL);
    dump_events();
    int render_end = first_ev(EV_RENDER_END), stop_at = first_ev(EV_STOP);
    bool ordered = render_end >= 0 && stop_at >= 0 && render_end < stop_at;
    if (stopped_early || !ordered) {
        printf("FAIL token-close-race: Close stopped platform before in-flight token "
               "release completed (stopped_early=%d render_end=%d stop=%d)\n",
               stopped_early, render_end, stop_at);
        env_release_token(&race_env);
        return 1;
    }
    printf("PASS token-close-race\n");
    env_release_token(&race_env);
    return 0;
}

static int cb_thread_started;
static void *callback_thread(void *arg) {
    (void)arg;
    OH_AVCodecCallback cb = g_cb;
    void *userdata = g_cb_userdata;
    OH_AVCodec *dec = g_codec;
    __atomic_store_n(&cb_thread_started, 1, __ATOMIC_RELEASE);
    pthread_mutex_lock(&block_lock); pthread_cond_broadcast(&block_cond); pthread_mutex_unlock(&block_lock);
    ev(EV_CALLBACK_ENTER);
    if (cb.onError) cb.onError(dec, AV_ERR_UNKNOWN, userdata);
    ev(EV_CALLBACK_EXIT);
    pthread_mutex_lock(&block_lock); pthread_cond_broadcast(&block_cond); pthread_mutex_unlock(&block_lock);
    return NULL;
}

static int mode_callback_inflight_close(void) {
    struct env *e = &race_env;
    if (env_start(e, false) < 0) return 70;
    stop_calls = 0; close_started = 0; close_done = 0;
    cb_thread_started = 0; watch_waiters = 0;
    watch_mutex = &e->s->output_mutex;
    ff_mutex_lock(&e->s->output_mutex);
    pthread_t bt, ct;
    pthread_create(&bt, NULL, callback_thread, NULL);
    if (timed_wait_flag(&cb_thread_started, 1000) != 0) return 1;
    if (timed_wait_flag(&watch_waiters, 1000) != 0) {
        printf("FAIL callback-inflight-close: callback did not reach the guarded body\n");
        ff_mutex_unlock(&e->s->output_mutex);
        return 1;
    }
    pthread_create(&ct, NULL, close_thread, NULL);
    if (timed_wait_flag(&close_started, 1000) != 0) return 1;
    int close_early = timed_wait_flag(&close_done, 120) == 0;
    ff_mutex_unlock(&e->s->output_mutex);
    pthread_join(bt, NULL);
    pthread_join(ct, NULL);
    watch_mutex = NULL;
    dump_events();
    int cb_exit = first_ev(EV_CALLBACK_EXIT);
    int stop_at = first_ev(EV_STOP);
    if (close_early || stop_calls == 0 || (cb_exit >= 0 && stop_at >= 0 && stop_at < cb_exit)) {
        printf("FAIL callback-inflight-close: Close did not wait for callback "
               "completion (close_early=%d stop=%d cb_exit=%d)\n",
               close_early, stop_at, cb_exit);
        return 1;
    }
    printf("PASS callback-inflight-close\n");
    return 0;
}

static int mode_prepare_fail(void) {
    struct env e;
    prepare_result = AV_ERR_UNKNOWN;
    int rc = env_start(&e, false);
    prepare_result = AV_ERR_OK;
    if (rc == 0) { printf("FAIL prepare-fail: start unexpectedly succeeded\n"); return 1; }
    oh_decode_close(&e.avctx);
    dump_events();
    int stops = count_ev(EV_STOP), destroys = count_ev(EV_DESTROY);
    if (stops != 0 || destroys != 1) {
        printf("FAIL prepare-fail: cleanup after Prepare failure must Destroy "
               "once without Stop (stops=%d destroys=%d)\n", stops, destroys);
        return 1;
    }
    printf("PASS prepare-fail\n");
    return 0;
}

static int mode_destroy_fail(void) {
    struct env e;
    if (env_start(&e, false) < 0) return 70;
    destroy_result = AV_ERR_UNKNOWN;
    oh_decode_close(&e.avctx);
    destroy_result = AV_ERR_OK;
    dump_events();
    if (destroy_calls != 1) {
        printf("FAIL destroy-fail: Destroy not attempted exactly once (%d)\n",
               destroy_calls);
        return 1;
    }
    struct env e2;
    int rc = env_start(&e2, false);
    if (rc == 0) {
        printf("FAIL destroy-fail: a new OHCodec decoder was created after a "
               "failed Destroy\n");
        oh_decode_close(&e2.avctx);
        return 1;
    }
    if (count_ev(EV_CREATE) != 1) {
        printf("FAIL destroy-fail: unexpected create attempts (%d)\n",
               count_ev(EV_CREATE));
        return 1;
    }
    printf("PASS destroy-fail\n");
    return 0;
}

static int mode_stop_fail(void) {
    struct env e;
    if (env_start(&e, false) < 0) return 70;
    stop_result = AV_ERR_UNKNOWN;
    oh_decode_close(&e.avctx);
    stop_result = AV_ERR_OK;
    dump_events();
    if (stop_calls != 1 || destroy_calls != 1) {
        printf("FAIL stop-fail: expected Stop and Destroy once (stop=%d destroy=%d)\n",
               stop_calls, destroy_calls);
        return 1;
    }
    struct env e2;
    int rc = env_start(&e2, false);
    if (rc == 0) {
        printf("FAIL stop-fail: a new OHCodec decoder was created after a "
               "failed Stop\n");
        oh_decode_close(&e2.avctx);
        return 1;
    }
    printf("PASS stop-fail\n");
    return 0;
}

static int mode_duplicate_close(void) {
    struct env e;
    if (env_start(&e, false) < 0) return 70;
    mutex_destroy_calls = cond_destroy_calls = 0;
    oh_decode_close(&e.avctx);
    int m1 = mutex_destroy_calls, c1 = cond_destroy_calls;
    oh_decode_close(&e.avctx);
    int m2 = mutex_destroy_calls, c2 = cond_destroy_calls;
    dump_events();
    if (m1 == 0 || c1 == 0 || m1 != m2 || c1 != c2) {
        printf("FAIL duplicate-close: second Close repeated cleanup "
               "(first mutex=%d cond=%d, second mutex=%d cond=%d)\n",
               m1, c1, m2, c2);
        return 1;
    }
    printf("PASS duplicate-close\n");
    return 0;
}

static int mode_consumer_handoff(void) {
    setenv("MP_OHCODEC_DIAGNOSTIC_MODE", "consumer-challenge", 1);
    test_same_consumer=true;
    struct env a,b,c;
    if(env_start(&a,false))return 2;
    uint64_t first=oh_decode_ref(a.s)->diagnostic_instance;
    int overlap=env_start(&b,false);
    int sets_before=count_ev(EV_SURFACE), starts_before=count_ev(EV_START);
    oh_decode_close(&b.avctx); oh_decode_close(&a.avctx);
    int old_destroy_index=nevents;
    int next=env_start(&c,false);
    uint64_t second=next?0:oh_decode_ref(c.s)->diagnostic_instance;
    bool pass=diagnostic_challenges==2 && overlap<0 && sets_before==1 && starts_before==1 && !next && first && second>first && count_ev(EV_SURFACE)==2 && count_ev(EV_START)==2 && events[old_destroy_index]==EV_CREATE;
    oh_decode_close(&c.avctx); dump_events();
    printf("%s consumer-handoff overlap=%d prior_sets=%d prior_starts=%d next=%d instance=%"PRIu64"/%"PRIu64"\n",pass?"PASS":"FAIL",overlap,sets_before,starts_before,next,first,second);
    return pass?0:1;
}

int main(int argc, char **argv) {
    if (argc != 2) return 64;
    if (!strcmp(argv[1], "close-held-frame")) return mode_close_held_frame();
    if (!strcmp(argv[1], "callback-after-close")) return mode_callback_after_close();
    if (!strcmp(argv[1], "token-close-race")) return mode_token_close_race();
    if (!strcmp(argv[1], "callback-inflight-close")) return mode_callback_inflight_close();
    if (!strcmp(argv[1], "consumer-handoff")) return mode_consumer_handoff();
    if (!strcmp(argv[1], "prepare-fail")) return mode_prepare_fail();
    if (!strcmp(argv[1], "duplicate-close")) return mode_duplicate_close();
    if (!strcmp(argv[1], "destroy-fail")) return mode_destroy_fail();
    if (!strcmp(argv[1], "stop-fail")) return mode_stop_fail();
    return 64;
}
