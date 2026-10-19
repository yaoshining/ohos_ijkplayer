#define _GNU_SOURCE
#include "integration.h"
#include <mpv/client.h>
#include <mpv/render.h>
#include <libavutil/avutil.h>
#include <libavformat/avformat.h>
#include <pthread.h>
#include <stdatomic.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>
#include <sys/stat.h>
#ifdef P21_HOST
#include <dlfcn.h>
#endif
#define W 640
#define H 360
struct render_state {mpv_handle *mpv;pthread_mutex_t lock;pthread_cond_t cond;int ready,rc;atomic_int stop,update;unsigned char pixels[W*H*4];};
static void render_update(void *arg){struct render_state *s=arg;atomic_store(&s->update,1);}
static void *render_thread(void *arg) {
 struct render_state *s=arg;mpv_render_context *ctx=NULL;int advanced=0;
 mpv_render_param create[]={{MPV_RENDER_PARAM_API_TYPE,MPV_RENDER_API_TYPE_SW},{MPV_RENDER_PARAM_ADVANCED_CONTROL,&advanced},{0,NULL}};
 int rc=mpv_render_context_create(&ctx,s->mpv,create);
 if(rc>=0)mpv_render_context_set_update_callback(ctx,render_update,s);
 pthread_mutex_lock(&s->lock);s->rc=rc;s->ready=1;pthread_cond_signal(&s->cond);pthread_mutex_unlock(&s->lock);
 if(rc<0)return NULL;
 unsigned char *pixels=calloc(1,W*H*4);if(!pixels){pthread_mutex_lock(&s->lock);s->rc=-1;pthread_mutex_unlock(&s->lock);mpv_render_context_free(ctx);return NULL;}
 int size[2]={W,H},block=0;size_t stride=W*4;
 mpv_render_param params[]={{MPV_RENDER_PARAM_SW_SIZE,size},{MPV_RENDER_PARAM_SW_FORMAT,"rgb0"},{MPV_RENDER_PARAM_SW_STRIDE,&stride},{MPV_RENDER_PARAM_SW_POINTER,pixels},{MPV_RENDER_PARAM_BLOCK_FOR_TARGET_TIME,&block},{0,NULL}};
 while(!atomic_load(&s->stop)) {
  if(atomic_exchange(&s->update,0))mpv_render_context_update(ctx);
  rc=mpv_render_context_render(ctx,params);
  pthread_mutex_lock(&s->lock);if(rc<0)s->rc=rc;memcpy(s->pixels,pixels,W*H*4);pthread_mutex_unlock(&s->lock);
  struct timespec pause={0,10000000};nanosleep(&pause,NULL);
 }
 free(pixels);mpv_render_context_free(ctx);return NULL;
}
static void event_log(mpv_event *e){if(e->event_id==MPV_EVENT_LOG_MESSAGE){mpv_event_log_message *m=e->data;fprintf(stderr,"[%s/%s] %s",m->prefix,m->level,m->text);}}
static void pump(mpv_handle *p,int millis){for(int i=0;i<millis/10;i++){mpv_event *e=mpv_wait_event(p,0.01);event_log(e);}}
static int command(mpv_handle *p,const char **args){int rc=mpv_command(p,args);if(rc<0)fprintf(stderr,"command %s: %s\n",args[0],mpv_error_string(rc));return rc;}
static int capture(struct render_state *s,const char *root,const char *name){char path[4096];snprintf(path,sizeof(path),"%s/%s.ppm",root,name);FILE *f=fopen(path,"wb");if(!f)return -1;fprintf(f,"P6\n%d %d\n255\n",W,H);pthread_mutex_lock(&s->lock);for(int i=0;i<W*H;i++)fwrite(s->pixels+i*4,1,3,f);int rc=s->rc;pthread_mutex_unlock(&s->lock);if(fclose(f))return -1;return rc;}
static void maps(const char *root){
#ifdef P21_HOST
 char path[4096],buf[8192];snprintf(path,sizeof(path),"%s/maps.txt",root);FILE *a=fopen("/proc/self/maps","r"),*b=fopen(path,"w");if(a&&b)while(fgets(buf,sizeof(buf),a))fputs(buf,b);if(a)fclose(a);if(b)fclose(b);
#else
 (void)root;
#endif
}
static int render(mpv_handle *p,const char *root,const char *mode){
 struct render_state *s=calloc(1,sizeof(*s));if(!s)return -1;s->mpv=p;pthread_mutex_init(&s->lock,NULL);pthread_cond_init(&s->cond,NULL);pthread_t thread;
 if(pthread_create(&thread,NULL,render_thread,s)){free(s);return -1;}
 pthread_mutex_lock(&s->lock);while(!s->ready)pthread_cond_wait(&s->cond,&s->lock);int rc=s->rc;pthread_mutex_unlock(&s->lock);
 if(rc<0)goto done;
 char ppm[4096],ass[4096];snprintf(ppm,sizeof(ppm),"%s/black.ppm",root);snprintf(ass,sizeof(ass),"%s/subtitle.ass",root);
 const char *load[]={"loadfile",ppm,NULL};if(command(p,load)<0){rc=-1;goto done;}
 int loaded=0;
 for(int i=0;i<500;i++){mpv_event *e=mpv_wait_event(p,0.01);event_log(e);if(e->event_id==MPV_EVENT_FILE_LOADED){loaded=1;break;}if(e->event_id==MPV_EVENT_END_FILE){fprintf(stderr,"early end file\n");break;}}
 if(!loaded){rc=-1;goto done;}pump(p,500);if(capture(s,root,"baseline")<0){rc=-1;goto done;}
 const char *sub[]={"sub-add",ass,"select",NULL};if(command(p,sub)<0){rc=-1;goto done;}pump(p,1000);if(capture(s,root,"subtitle")<0){rc=-1;goto done;}
 const char *hide[]={"set","sub-visibility","no",NULL};if(command(p,hide)<0){rc=-1;goto done;}
 const char *osd[]={"show-text",!strcmp(mode,"cjk")?"\xe4\xb8\xad":"ABC abc 012","10000",NULL};if(command(p,osd)<0){rc=-1;goto done;}pump(p,1000);rc=capture(s,root,"osd");maps(root);
 done:atomic_store(&s->stop,1);pthread_join(thread,NULL);pump(p,100);pthread_cond_destroy(&s->cond);pthread_mutex_destroy(&s->lock);free(s);return rc;
}
int main(int argc,char **argv){
 if(argc<3){fprintf(stderr,"usage: phase21-probe ROOT init|repeat|conflict|late|render|no-font|cjk [SECOND_ROOT]\n");return 2;}
 char conf[4096],state[4096],cache[4096],res[4096];snprintf(conf,sizeof(conf),"%s/smb.conf",argv[1]);snprintf(state,sizeof(state),"%s/state",argv[1]);snprintf(cache,sizeof(cache),"%s/cache",argv[1]);snprintf(res,sizeof(res),"%s/resources",argv[1]);
 struct p21_config c={conf,state,cache,res};struct p21_error e;mpv_handle *p=NULL;
#ifdef P21_HOST
 void *legacy=NULL;int (*smbfree)(void*,int)=NULL;
 if(!strcmp(argv[2],"late")){void *(*smbnew)(void)=dlsym(RTLD_DEFAULT,"smbc_new_context");smbfree=dlsym(RTLD_DEFAULT,"smbc_free_context");if(!smbnew||!smbfree)return 3;legacy=smbnew();if(!legacy)return 4;}
#endif
 int rc=p21_create(&c,&p,&e);fprintf(stderr,"create stage=%s code=%d mpv_api=%lu ffmpeg=%s\n",e.stage,e.code,mpv_client_api_version(),av_version_info());
#ifdef P21_HOST
 if(!strcmp(argv[2],"late")){maps(argv[1]);if(legacy)smbfree(legacy,1);if(p)p21_destroy(&p);return rc<0&&!strcmp(e.stage,"samba")&&e.code==EBUSY?0:5;}
#endif
 if(rc<0)return 1;
#ifdef P21_HOST
 if(!strcmp(argv[2],"cache-write")||!strcmp(argv[2],"cache-denied")) {
  void *(*newctx)(void)=dlsym(RTLD_DEFAULT,"smbc_new_context");void *(*initctx)(void*)=dlsym(RTLD_DEFAULT,"smbc_init_context");int (*freectx)(void*,int)=dlsym(RTLD_DEFAULT,"smbc_free_context");bool (*cache_set)(const char*,const char*,time_t)=dlsym(RTLD_DEFAULT,"gencache_set");
  if(!newctx||!initctx||!freectx||!cache_set){p21_destroy(&p);return 11;}
  void *ctx=newctx();if(!ctx||!initctx(ctx)){if(ctx)freectx(ctx,1);p21_destroy(&p);return 12;}
  char lock[4096];snprintf(lock,sizeof(lock),"%s/lock",c.state_root);int denied=!strcmp(argv[2],"cache-denied");
  if(denied&&chmod(lock,0500)){freectx(ctx,1);p21_destroy(&p);return 13;}
  errno=0;bool ok=cache_set("PHASE21_KEY","phase21-value",time(NULL)+60);int saved=errno;
  fprintf(stderr,"cache result=%d errno=%d denied=%d\n",ok,saved,denied);maps(argv[1]);
  if(denied&&chmod(lock,0700)){freectx(ctx,1);p21_destroy(&p);return 14;}
  int fr=freectx(ctx,1);p21_destroy(&p);return fr==0&&ok==!denied?0:15;
 }
#endif
 if(mpv_request_log_messages(p,"debug")<0){p21_destroy(&p);return 6;}
 if(!strcmp(argv[2],"repeat")){p21_destroy(&p);p21_destroy(&p);if(p21_create(&c,&p,&e))return 7;}
 if(!strcmp(argv[2],"conflict")){if(argc!=4){p21_destroy(&p);return 2;}char other[4096];snprintf(other,sizeof(other),"%s/smb.conf",argv[3]);c.config_file=other;mpv_handle *q=NULL;rc=p21_create(&c,&q,&e);fprintf(stderr,"conflict stage=%s code=%d\n",e.stage,e.code);if(q)p21_destroy(&q);p21_destroy(&p);return rc<0&&!strcmp(e.stage,"samba")&&e.code==EBUSY?0:8;}
 if(!strcmp(argv[2],"no-font")){char font[4096];snprintf(font,sizeof(font),"%s/resources/fonts/font1.ttf",argv[1]);if(unlink(font)){p21_destroy(&p);return 9;}}
 if(!strcmp(argv[2],"render")||!strcmp(argv[2],"no-font")||!strcmp(argv[2],"cjk"))rc=render(p,argv[1],argv[2]);
 maps(argv[1]);p21_destroy(&p);return rc<0?10:0;
}
