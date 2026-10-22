/* Public extension wrapper; no ownership of mpv/client/VO/log objects. */
#include <mpv/ohcodec_terminal.h>
#include "ohcodec_terminal.h"
#include <stdatomic.h>
#include <errno.h>
#include <string.h>
static atomic_int public_registration;
static mpv_ohcodec_terminal_handler handler;
static void *opaque;
static mpv_ohcodec_terminal_record published;
static void convert(mpv_ohcodec_terminal_record *out,const struct mp_ohcodec_terminal_record *in)
{
    *out=(mpv_ohcodec_terminal_record){.size=sizeof(*out),.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION,
        .platform_error=in->platform_error,.stage=in->stage,.owner_tag=in->owner_tag};
}
static void receive(const struct mp_ohcodec_terminal_record *in,void *unused)
{
    (void)unused;
    convert(&published,in);
    handler(&published,opaque);
}
uint32_t mpv_ohcodec_terminal_api_version(void) {return MPV_OHCODEC_TERMINAL_ABI_VERSION;}
int mpv_ohcodec_terminal_register(const mpv_ohcodec_terminal_config *c)
{
    if(!c || c->size<sizeof(*c) || c->abi_version!=MPV_OHCODEC_TERMINAL_ABI_VERSION || !c->handler)
        return MPV_ERROR_INVALID_PARAMETER;
    for(unsigned i=0;i<4;i++)if(c->reserved[i])return MPV_ERROR_INVALID_PARAMETER;
    int expected=0;
    if(!atomic_compare_exchange_strong_explicit(&public_registration,&expected,1,memory_order_acq_rel,memory_order_acquire))
        return MPV_ERROR_INVALID_PARAMETER;
    handler=c->handler;opaque=c->opaque;
    int rc=mp_ohcodec_terminal_register(receive,NULL);
    if(rc){handler=NULL;opaque=NULL;atomic_store_explicit(&public_registration,0,memory_order_release);return MPV_ERROR_GENERIC;}
    atomic_store_explicit(&public_registration,2,memory_order_release);
    return 0;
}
int mpv_ohcodec_terminal_enable(void)
{
    if(atomic_load_explicit(&public_registration,memory_order_acquire)!=2)return MPV_ERROR_UNINITIALIZED;
    return mp_ohcodec_terminal_enable()?0:MPV_ERROR_GENERIC;
}
int mpv_ohcodec_terminal_snapshot(mpv_ohcodec_terminal_record *out)
{
    if(!out || out->size<sizeof(*out) || out->abi_version!=MPV_OHCODEC_TERMINAL_ABI_VERSION)return MPV_ERROR_INVALID_PARAMETER;
    for(unsigned i=0;i<4;i++)if(out->reserved[i])return MPV_ERROR_INVALID_PARAMETER;
    struct mp_ohcodec_terminal_record in;
    if(!mp_ohcodec_terminal_snapshot(&in))return 0;
    convert(out,&in);return 1;
}
