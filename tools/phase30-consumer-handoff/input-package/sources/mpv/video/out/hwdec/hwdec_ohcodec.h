/* HarmonyOS OHCodec Surface interop. */
#pragma once

#include <stdbool.h>

#include <libavcodec/ohcodec_buffer.h>
#include <native_image/native_image.h>

#include "osdep/threads.h"
#include "video/out/gpu/hwdec.h"

struct ohcodec_surface {
    OH_NativeImage *image;
    OHNativeWindow *window;
    mp_mutex lock;
    mp_cond cond;
    unsigned pending;
    bool initialized;
};

enum {
    OHCODEC_DRAIN_NOT_APPLICABLE = 0,
    OHCODEC_DRAIN_SAFE = 1,
    OHCODEC_DRAIN_SAFE_RELEASE_ERROR = 2,
    OHCODEC_DRAIN_UNSAFE = 3,
};

enum {
    OHCODEC_DRAIN_REASON_SEEK = 1,
    OHCODEC_DRAIN_REASON_CLOSE = 2,
    OHCODEC_DRAIN_REASON_REINIT = 3,
    OHCODEC_DRAIN_REASON_RESUME = 4,
};

struct ohcodec_interop {
    void (*owner_uninit)(struct ra_hwdec *hw);
    bool (*mapper_init)(struct ra_hwdec_mapper *mapper);
    void (*mapper_uninit)(struct ra_hwdec_mapper *mapper);
    int (*map)(struct ra_hwdec_mapper *mapper);
    int (*reuse)(struct ra_hwdec_mapper *mapper);
    void (*unmap)(struct ra_hwdec_mapper *mapper);
    void (*release)(struct ra_hwdec_mapper *mapper);
    /* Phase28: synchronously finish GPU work for this mapper, return the
     * acquired consumer buffer, and release retained frame references. */
    int (*drain)(struct ra_hwdec_mapper *mapper, int reason,
                 int *platform_error);
};

struct ohcodec_priv {
    struct mp_hwdec_ctx hwctx;
    struct ohcodec_surface *surface;
    void *interop_owner_priv;
    const struct ohcodec_interop *interop;
    /* Surface/owner-scoped terminal state: a release failure forbids a new
     * OHCodec producer on this Surface even after the decoder is recreated. */
    bool surface_invalid;
#ifdef MP_OHCODEC_HANDOFF_TRACE
    uint64_t trace_owner, trace_consumer;
#endif
#ifdef MP_OHCODEC_DIAGNOSTIC
    uint64_t diagnostic_owner;
    uint64_t diagnostic_consumer;
#endif
};

struct ohcodec_mapper_priv {
    void *priv;
    AVOHCodecBuffer *last_token;
    int terminal_drain_error; /* First UNSAFE cause; cannot be cleared by retry. */
    struct mp_image *last_src;
};

typedef bool (*ohcodec_interop_init)(struct ra_hwdec *hw);

#ifdef MP_OHCODEC_DIAGNOSTIC
/*
 * Diagnostic-only terminal barrier.  After the first known UNSAFE completion
 * the VO thread must not return to the core/parent teardown.  This function
 * logs the retained state and blocks until an external bounded process stop;
 * the experiment build aborts at the same point instead.  It never returns.
 */
void ohcodec_terminal_barrier(struct mp_log *log, const char *site);
#endif

bool ohcodec_surface_init(struct ohcodec_surface *surface,
                          OH_NativeImage *image);
void ohcodec_surface_destroy(struct ohcodec_surface *surface);
bool ohcodec_surface_wait(struct ohcodec_surface *surface,
                          struct mp_log *log, int64_t *wait_ns);

bool ohcodec_interop_gl_init(struct ra_hwdec *hw);
bool ohcodec_interop_pl_init(struct ra_hwdec *hw);

/* Returns an OHCODEC_DRAIN_* result. NOT_APPLICABLE means the active interop
 * has no Vulkan consumer buffers (GL/software) and must not modify state. */
int ohcodec_mapper_drain(struct ra_hwdec_mapper *mapper, int reason,
                         int *platform_error);
bool ohcodec_mapper_can_drain(struct ra_hwdec_mapper *mapper);
bool ohcodec_mapper_surface_invalid(struct ra_hwdec_mapper *mapper);
void ohcodec_mapper_mark_surface_invalid(struct ra_hwdec_mapper *mapper);
bool ohcodec_hwdec_surface_invalid(struct ra_hwdec *hw);
void ohcodec_hwdec_mark_surface_invalid(struct ra_hwdec *hw);
struct ra_hwdec *ohcodec_hwdec_find(struct ra_hwdec **hwdecs, int num);
