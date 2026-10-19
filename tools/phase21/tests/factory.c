#include "integration.h"
#include "mpv/client.h"
#include "libavformat/ohcodec_smb_runtime.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
struct mpv_handle { int alive; }; static struct mpv_handle object;
static int scenario, sequence, freed, options, initialized, samba_calls, seen;
int p21_validate(const struct p21_config *c, struct p21_error *e) {assert(c);assert(sequence++==0);if(scenario==1){e->stage="resources";e->code=ENOENT;return -1;}return 0;}
int ohcodec_smb_runtime_configure_v1(const struct ohcodec_smb_runtime_v1 *c) {assert(sequence++==1);assert(c->struct_size==sizeof(*c));assert(!strcmp(c->state_root,"/state"));samba_calls++;if(scenario==2){errno=EBUSY;return -1;}return 0;}
mpv_handle *mpv_create(void){assert(sequence++==2);if(scenario==3)return NULL;object.alive=1;return &object;}
int mpv_set_option_string(mpv_handle *p,const char *k,const char *v){assert(p==&object&&p->alive);assert(sequence>=3);assert(!initialized);options++;
 const char *keys[]={"config","sub-font-provider","osd-font-provider","sub-fonts-dir","osd-fonts-dir","demuxer-cache-dir"};const char *values[]={"no","none","none","/resources/fonts","/resources/fonts","/cache/demux"};for(int i=0;i<6;i++)if(!strcmp(k,keys[i])){assert(!strcmp(v,values[i]));seen|=1<<i;}if(!strcmp(k,"sub-font-provider")||!strcmp(k,"osd-font-provider"))assert(!strcmp(v,"none"));return scenario==4||(scenario==6&&options==20)?-7:0;}
int mpv_initialize(mpv_handle *p){assert(p->alive);assert(options>=20);assert(seen==63);initialized++;return scenario==5?-9:0;}
void mpv_terminate_destroy(mpv_handle *p){assert(p==&object&&p->alive);p->alive=0;freed++;}
int main(int argc,char **argv){assert(argc==2);sscanf(argv[1],"%d",&scenario);struct p21_config c={"/config","/state","/cache","/resources"};struct p21_error e={0};mpv_handle *p=(void*)123;if(scenario==7){assert(p21_create(NULL,&p,&e)<0&&p==NULL&&e.code==EINVAL);assert(sequence==0);puts("NULL config PASS");return 0;}if(scenario==8){assert(p21_create(&c,NULL,NULL)<0&&sequence==0);puts("NULL out PASS");return 0;}if(scenario==9){assert(p21_create(&c,&p,NULL)==0);p21_destroy(&p);assert(freed==1);puts("NULL error PASS");return 0;}int rc=p21_create(&c,&p,&e);
 if(scenario){assert(rc<0);assert(p==NULL);assert(e.code!=0);assert(freed==(scenario>=4));assert(initialized==(scenario==5));assert(samba_calls==(scenario>=2));}
 else {assert(rc==0&&p==&object);assert(initialized==1);p21_destroy(&p);assert(p==NULL&&freed==1);p21_destroy(&p);assert(freed==1);}
 puts("factory PASS");return 0;}
