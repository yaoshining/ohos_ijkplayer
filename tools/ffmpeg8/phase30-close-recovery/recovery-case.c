/* Included after Phase30's platform doubles and actual FFmpeg functions. */
#include <assert.h>

static void deliver_old_callbacks(OH_AVCodecCallback cb, OH_AVCodec *dec,
                                  void *userdata, OH_AVBuffer *buf)
{
    OH_AVFormat format = {0};
    cb.onNeedInputBuffer(dec, 3, buf, userdata);
    cb.onNewOutputBuffer(dec, 3, buf, userdata);
    cb.onError(dec, AV_ERR_UNKNOWN, userdata);
    cb.onStreamChanged(dec, &format, userdata);
}

static struct env *closing_env;

static void deliver_during_failure(void)
{
    OHCodecDecContext *s = closing_env->s;
    OH_AVBuffer buffer = {0};
    deliver_old_callbacks(g_cb, g_codec, g_cb_userdata, &buffer);
    assert(s->decode_status == 0 && s->input_queue->count == 1 && s->output_queue->count == 1);
}

static int test_recovery(bool fail_destroy, bool original)
{
    struct env a, b, reuse;
    OH_AVBuffer payload = {0}, next_payload = {0};
    test_same_consumer = true;
    shared_device.native_window = &old_window;
    assert(env_start(&a, true) == 0);
    OHCodecDecRef *old = g_cb_userdata;
    OH_AVCodec *old_dec = g_codec;
    OH_AVCodecCallback old_cb = g_cb;
    old_cb.onNeedInputBuffer(old_dec, 3, &payload, old);
    old_cb.onNewOutputBuffer(old_dec, 3, &payload, old);
    assert(a.s->input_queue->count == 1 && a.s->output_queue->count == 1);
    AVOHCodecBuffer discard = {
        .index = 4, .dec_ref = av_buffer_ref(a.s->dec_ref),
        .generation = a.token->generation,
    };
    atomic_init(&discard.released, false);
    closing_env = &a;
    on_injected_error = deliver_during_failure;
    stop_result = fail_destroy ? AV_ERR_OK : AV_ERR_UNKNOWN;
    destroy_result = fail_destroy ? AV_ERR_UNKNOWN : AV_ERR_OK;
    oh_decode_close(&a.avctx);
    oh_decode_close(&a.avctx);
    assert(stop_calls == 1 && destroy_calls == 1);
    assert(!a.s->input_queue && !a.s->output_queue && !a.s->dec_ref && !a.s->dec);
    assert(old->detached && !old->attached && !old->active);
    assert(old->generation != a.token->generation);
    free(a.s);
    a.avctx.priv_data = NULL;
    stop_result = destroy_result = AV_ERR_OK;

    shared_device.native_window = &new_window;
    int rc = env_start(&b, true);
    printf("pid=%ld injection=%s old_surface=17 new_surface=18 "
           "second_start=%d create_calls=%d\n", (long)getpid(),
           fail_destroy ? "Destroy" : "Stop", rc, count_ev(EV_CREATE));
    assert(av_ohcodec_release_buffer(a.token, 1) == AVERROR(ESTALE));
    assert(av_ohcodec_release_buffer(a.token, 0) == 0);
    assert(av_ohcodec_release_buffer(&discard, 0) == 0);
    av_buffer_unref(&discard.dec_ref);
    env_release_token(&a);
    assert(render_calls == 0 && free_calls == 0);
    if (fail_destroy)
        deliver_old_callbacks(old_cb, old_dec, old, &payload);
    if (original) {
        assert(rc == AVERROR_EXTERNAL && count_ev(EV_CREATE) == 1 && count_ev(EV_SURFACE) == 1);
        oh_decode_close(&b.avctx);
        return 0;
    }
    assert(rc == 0 && count_ev(EV_START) == 2 && count_ev(EV_SURFACE) == 2);
    assert(old_window.refs == (int)fail_destroy && new_window.refs == 1);
    assert(b.s->decode_status == 0 && b.s->input_queue->count == 0 && b.s->output_queue->count == 0);
    g_cb.onNewOutputBuffer(g_codec, 3, &next_payload, g_cb_userdata);
    assert(b.s->output_queue->count == 1);
    assert(av_ohcodec_release_buffer(b.token, 1) == 0 && render_calls == 1);
    assert(last_render_dec == b.s->dec && last_render_index == 3);
    oh_decode_close(&b.avctx);
    env_release_token(&b);
    assert(new_window.refs == 0);

    /* Different wrapper, same old Surface ID. Destroy is the release boundary. */
    shared_device.native_window = &alias_window;
    int sets = count_ev(EV_SURFACE);
    int reused = env_start(&reuse, false);
    assert((reused < 0) == fail_destroy);
    assert(count_ev(EV_SURFACE) == sets + !fail_destroy);
    oh_decode_close(&reuse.avctx);
    assert(alias_window.refs == 0 && old_window.refs == (int)fail_destroy);
    dump_events();
    return 0;
}
