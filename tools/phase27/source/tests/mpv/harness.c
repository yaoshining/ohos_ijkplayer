#include <time.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
// Only external dependencies are stubbed. Actual production functions follow below.
typedef struct {int unused;} OHNativeWindow;
typedef int OH_NativeBuffer_ColorSpace;
typedef int OH_NativeBuffer_MetadataType;
enum {PL_COLOR_TRC_PQ=1,PL_COLOR_TRC_HLG=2,PL_COLOR_PRIM_BT_2020=3,OH_COLORSPACE_DISPLAY_BT2020_PQ=4,OH_COLORSPACE_DISPLAY_BT2020_HLG=5,OH_COLORSPACE_DISPLAY_SRGB=6,OH_VIDEO_HDR_HLG=7,OH_VIDEO_HDR_HDR10=8,OH_VIDEO_NONE=9,OH_HDR_METADATA_TYPE=10,OH_HDR_STATIC_METADATA=11,SET_HDR_WHITE_POINT_BRIGHTNESS=12};
struct xy {float x,y;};
struct pl_raw_primaries {struct xy red,green,blue,white;};
struct pl_hdr_metadata {struct pl_raw_primaries prim;float max_luma,min_luma,max_cll,max_fall;};
struct pl_color_space {int transfer,primaries;struct pl_hdr_metadata hdr;};
struct color_repr {void *dovi; int sys, levels, alpha;};
struct rect {int x0,y0,x1,y1;};
struct mp_image_params {int imgfmt,hw_subfmt,w,h,p_w,p_h,force_window;struct pl_color_space color;struct color_repr repr;int light,chroma_location,vflip,rotate,stereo3d;struct rect crop;};
typedef struct {struct {struct xy displayPrimaryRed,displayPrimaryGreen,displayPrimaryBlue,whitePoint;float maxLuminance,minLuminance;} smpte2086;struct {float maxContentLightLevel,maxFrameAverageLightLevel;} cta861;} OH_NativeBuffer_StaticMetadata;
struct vo_ohos_state;
struct vo {struct vo_ohos_state *ohos;struct mp_image_params current;};
static const struct pl_color_space pl_color_space_srgb={0};
static const struct pl_raw_primaries prim={.red={.x=.708f,.y=.292f},.green={.x=.170f,.y=.797f},.blue={.x=.131f,.y=.046f},.white={.x=.3127f,.y=.3290f}};
static bool pl_primaries_valid(const struct pl_raw_primaries *p){return p->red.x>0;}
static const struct pl_raw_primaries *pl_raw_primaries_get(int p){(void)p;return &prim;}
static void pl_color_space_infer(struct pl_color_space *p){(void)p;} // fully specified input; no inference tested
static struct mp_image_params vo_get_current_params(struct vo *v){return v->current;}
static bool pl_color_space_equal(const struct pl_color_space*a,const struct pl_color_space*b){return a->transfer==b->transfer&&a->primaries==b->primaries&&!memcmp(&a->hdr,&b->hdr,sizeof(a->hdr));}
static bool pl_color_repr_equal(const struct color_repr*a,const struct color_repr*b){return a->dovi==b->dovi;}
static bool mp_rect_equals(const struct rect*a,const struct rect*b){return a->x0==b->x0&&a->y0==b->y0&&a->x1==b->x1&&a->y1==b->y1;}
#define MP_VERBOSE(...) ((void)0)
#define MP_WARN(...) ((void)0)
#define MP_INFO(...) ((void)0)
static int static_calls,type_calls,color_calls,fail_static;static float last_peak,last_cll;
static int OH_NativeWindow_SetColorSpace(OHNativeWindow*w,int c){(void)w;(void)c;color_calls++;return 0;}
static int OH_NativeWindow_SetMetadataValue(OHNativeWindow*w,int key,int n,uint8_t*p){(void)w;if(key==OH_HDR_STATIC_METADATA){if(n!=(int)sizeof(OH_NativeBuffer_StaticMetadata))abort();OH_NativeBuffer_StaticMetadata m;memcpy(&m,p,sizeof(m));static_calls++;if(fail_static){fail_static--;return -1;}last_peak=m.smpte2086.maxLuminance;last_cll=m.cta861.maxContentLightLevel;printf("STUB_STATIC_SET call=%d peak=%.0f cll=%.0f\n",static_calls,last_peak,last_cll);}else if(key==OH_HDR_METADATA_TYPE){type_calls++;}else abort();return 0;}
static int OH_NativeWindow_NativeWindowHandleOpt(OHNativeWindow*w,int op,...){(void)w;(void)op;return 0;}

#define PL_API_VER 344
enum pl_alpha_mode {PL_ALPHA_UNKNOWN, PL_ALPHA_NONE, PL_ALPHA_INDEPENDENT};
enum { PL_COLOR_SYSTEM_RGB=1, PL_COLOR_LEVELS_FULL=1 };
struct ra_swapchain;
struct swap_fns {void (*set_color)(struct ra_swapchain*,struct mp_image_params*);};
struct ra_swapchain {const struct swap_fns *fns;struct vo *vo;};
struct ra_ctx {struct ra_swapchain *swapchain;struct {bool want_alpha;} opts;};
struct priv {struct ra_ctx *ra_ctx;int output_levels;void *sw;};
static void pl_swapchain_colorspace_hint(void *s,struct pl_color_space*h){(void)s;(void)h;abort();}

#include "actual-functions.inc"
static struct mp_image_params fixture(float peak){struct mp_image_params p={0};p.w=1920;p.h=1080;p.p_w=1;p.p_h=1;p.imgfmt=1;p.color.transfer=PL_COLOR_TRC_PQ;p.color.primaries=PL_COLOR_PRIM_BT_2020;p.color.hdr.prim=prim;p.color.hdr.max_luma=peak;p.color.hdr.min_luma=.005f;p.color.hdr.max_cll=1000;p.color.hdr.max_fall=400;return p;}

static void bridge(struct ra_swapchain *sw,struct mp_image_params *params) { vo_ohos_set_color(sw->vo,params); }
int main(int argc,char **argv) {
 if(argc!=2)return 64;
 struct mp_image_params original=fixture(1000),current=fixture(2000);
 original.color.hdr.max_cll=current.color.hdr.max_cll=1000;
 struct vo_ohos_state ctx={0}; OHNativeWindow window={0};ctx.native_window=&window;
 struct vo vo={.ohos=&ctx,.current=original};
 struct swap_fns fns={.set_color=bridge};struct ra_swapchain sw={.fns=&fns,.vo=&vo};
 struct ra_ctx ra={.swapchain=&sw};struct priv p={.ra_ctx=&ra};
 struct pl_color_space hint=current.color;
 if(!strcmp(argv[1],"first-failure") || !strcmp(argv[1],"transition-failure") || !strcmp(argv[1],"invalidate-failure")) {
  vo.current=current;
  if(strcmp(argv[1],"first-failure"))set_colorspace_hint(&p,&hint);
  if(!strcmp(argv[1],"transition-failure")){hint.transfer=PL_COLOR_TRC_HLG;vo.current.color=hint;}
  if(!strcmp(argv[1],"invalidate-failure"))vo_ohos_invalidate_color(&vo);
  int before=static_calls;fail_static=1;set_colorspace_hint(&p,&hint);
  if(static_calls!=before+1)return 30;
  set_colorspace_hint(&p,&hint);if(static_calls!=before+2)return 31;
  set_colorspace_hint(&p,&hint);return static_calls==before+2?0:32;
 }
 if(!strcmp(argv[1],"cache") || !strcmp(argv[1],"retry") || !strcmp(argv[1],"invalidate") || !strcmp(argv[1],"transitions") || !strncmp(argv[1],"field-",6)) {
  vo.current=current;set_colorspace_hint(&p,&hint);if(static_calls!=1)return 10;
  set_colorspace_hint(&p,&hint);if(static_calls!=1)return 11;
  if(!strcmp(argv[1],"cache")) {hint.hdr.max_luma=2500;vo.current.color=hint;set_colorspace_hint(&p,&hint);return static_calls==2&&last_peak==2500?0:12;}
  if(!strcmp(argv[1],"retry")) {hint.hdr.max_luma=2500;vo.current.color=hint;fail_static=1;set_colorspace_hint(&p,&hint);if(static_calls!=2||last_peak!=2000)return 13;set_colorspace_hint(&p,&hint);if(static_calls!=3||last_peak!=2500)return 14;set_colorspace_hint(&p,&hint);return static_calls==3?0:15;}
  if(!strcmp(argv[1],"invalidate")) {vo_ohos_invalidate_color(&vo);set_colorspace_hint(&p,&hint);return static_calls==2?0:16;}
  if(!strcmp(argv[1],"transitions")) {hint.transfer=PL_COLOR_TRC_HLG;vo.current.color=hint;set_colorspace_hint(&p,&hint);if(static_calls!=2)return 17;hint=pl_color_space_srgb;set_colorspace_hint(&p,&hint);if(static_calls!=2||ctx.static_metadata_valid)return 18;hint=current.color;set_colorspace_hint(&p,&hint);return static_calls==3?0:19;}
  float *fields[]={&hint.hdr.prim.red.x,&hint.hdr.prim.red.y,&hint.hdr.prim.green.x,&hint.hdr.prim.green.y,&hint.hdr.prim.blue.x,&hint.hdr.prim.blue.y,&hint.hdr.prim.white.x,&hint.hdr.prim.white.y,&hint.hdr.max_luma,&hint.hdr.min_luma,&hint.hdr.max_cll,&hint.hdr.max_fall};
  int n=atoi(argv[1]+6);if(n<0||n>=12)return 64;*fields[n]+=.001f;vo.current.color=hint;set_colorspace_hint(&p,&hint);if(static_calls!=2)return 20;set_colorspace_hint(&p,&hint);return static_calls==2?0:21;
 }
 if(!strcmp(argv[1],"stale-current")) {
  // Simulate static_equal's real no-reconfig outcome: vo.current remains original.
  if(!mp_image_params_static_equal(&original,&current))return 2;
  vo_ohos_invalidate_color(&vo); // neutralizes the independently known cache bug
  set_colorspace_hint(&p,&hint);
  bool ok=static_calls==1&&last_peak==2000&&last_cll==1000;
  printf("stale-current: actual_hint=%.0f expected_window=2000 actual_window=%.0f cll=%.0f result=%s\n",hint.hdr.max_luma,last_peak,last_cll,ok?"PASS":"FAIL");return ok?0:1;
 }
 if(!strcmp(argv[1],"target-limited")) {
  vo.current=current; hint.hdr.max_luma=600;hint.hdr.max_cll=600;hint.hdr.max_fall=0;
  set_colorspace_hint(&p,&hint);
  bool ok=static_calls==1&&last_peak==600&&last_cll==600;
  printf("target-limited: actual_hint=%.0f expected_window=600 actual_window=%.0f result=%s\n",hint.hdr.max_luma,last_peak,ok?"PASS":"FAIL");return ok?0:1;
 }
 if(!strcmp(argv[1],"sdr-output")) {
  hint=pl_color_space_srgb;set_colorspace_hint(&p,&hint);
  bool ok=static_calls==0&&ctx.metadata_type_valid&&ctx.metadata_type==OH_VIDEO_NONE&&ctx.color_space==OH_COLORSPACE_DISPLAY_SRGB;
  printf("sdr-output: static_calls=%d metadata_type=%d result=%s\n",static_calls,ctx.metadata_type,ok?"PASS":"FAIL");return ok?0:1;
 }
 if(!strcmp(argv[1],"matching-control")) {
  vo.current=current;set_colorspace_hint(&p,&hint);
  bool ok=last_peak==2000&&last_cll==1000;printf("matching-control: result=%s\n",ok?"PASS":"FAIL");return ok?0:1;
 }
 return 64;
}
