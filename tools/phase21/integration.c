#include "integration.h"
#include <mpv/client.h>
#include <libavformat/ohcodec_smb_runtime.h>
#include <errno.h>
#include <stdio.h>
int p21_create(const struct p21_config *c, mpv_handle **out, struct p21_error *e)
{
    struct p21_error ignored; if (!e) e=&ignored;
    e->stage="arguments";e->code=EINVAL;
    if (!out) return -1;
    *out=NULL; if (!c) return -1;
    if (p21_validate(c,e)) return -1;
    struct ohcodec_smb_runtime_v1 s={sizeof(s),c->config_file,c->state_root,c->cache_root,c->resource_root};
    if (ohcodec_smb_runtime_configure_v1(&s)) {e->stage="samba";e->code=errno;return -1;}
    mpv_handle *p=mpv_create();
    if (!p) {e->stage="create";e->code=ENOMEM;return -1;}
    char fonts[4096],cache[4096];
    int n=snprintf(fonts,sizeof(fonts),"%s/fonts",c->resource_root);
    int m=snprintf(cache,sizeof(cache),"%s/demux",c->cache_root);
    if (n<0||m<0||(size_t)n>=sizeof(fonts)||(size_t)m>=sizeof(cache)) {e->stage="resources";e->code=ENAMETOOLONG;goto fail;}
    const char *options[][2]={
      {"config","no"},{"load-scripts","no"},{"sub-auto","no"},{"embeddedfonts","no"},
      {"sub-font-provider","none"},{"osd-font-provider","none"},
      {"sub-fonts-dir",fonts},{"osd-fonts-dir",fonts},
      {"sub-font","Pixel Operator Mono"},{"osd-font","Pixel Operator Mono"},
      {"sub-bold","yes"},{"osd-bold","yes"},{"demuxer-cache-dir",cache},
      {"vo","libmpv"},{"ao","null"},{"idle","yes"},{"keep-open","yes"},
      {"image-display-duration","30"},{"pause","yes"},{"terminal","no"},
      {"osd-level","0"},{"sub-ass-override","force"},{"sub-font-size","32"},{"osd-font-size","32"},
    };
    for (size_t i=0;i<sizeof(options)/sizeof(options[0]);i++) {
      int rc=mpv_set_option_string(p,options[i][0],options[i][1]);
      if (rc<0) {e->stage=options[i][0];e->code=rc;goto fail;}
    }
    int rc=mpv_initialize(p);
    if (rc<0) {e->stage="initialize";e->code=rc;goto fail;}
    *out=p;e->stage="ready";e->code=0;return 0;
fail:
    mpv_terminate_destroy(p);return -1;
}
void p21_destroy(mpv_handle **p) {if(p&&*p){mpv_handle *old=*p;*p=NULL;mpv_terminate_destroy(old);}}
