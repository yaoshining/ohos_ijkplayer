#define _GNU_SOURCE
#include "integration.h"
#include <libavutil/avutil.h>
#include <libavutil/sha.h>
#include <libavutil/mem.h>
#include <mpv/client.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
int p22_mode(const char*);
static int maps(const char *root){
 char path[4096],buf[8192];snprintf(path,sizeof(path),"%s/maps.txt",root);
 FILE *a=fopen("/proc/self/maps","r");if(!a)return -1;FILE *b=fopen(path,"w");if(!b){fclose(a);return -1;}
 while(fgets(buf,sizeof(buf),a))if(fputs(buf,b)<0){fclose(a);fclose(b);return -1;}
 int rc=ferror(a);fclose(a);return fclose(b)||rc?-1:0;
}
int main(int argc,char **argv){
 if(argc<3||!p22_mode(argv[2])){fprintf(stderr,"unsupported target mode\n");return 64;}
 int mode=p22_mode(argv[2]);if((mode==3&&argc!=4)||(mode!=3&&argc!=3))return 64;
 char conf[4096],state[4096],cache[4096],res[4096];
 if(strlen(argv[1])>4000)return 64;
 snprintf(conf,sizeof(conf),"%s/smb.conf",argv[1]);snprintf(state,sizeof(state),"%s/state",argv[1]);snprintf(cache,sizeof(cache),"%s/cache",argv[1]);snprintf(res,sizeof(res),"%s/resources",argv[1]);
 struct p21_config c={conf,state,cache,res};struct p21_error e;mpv_handle *p=NULL;
 int rc=p21_create(&c,&p,&e);fprintf(stderr,"mode=%s create stage=%s code=%d mpv_api=%lu ffmpeg=%s\n",argv[2],e.stage,e.code,mpv_client_api_version(),av_version_info());
 if(maps(argv[1])){p21_destroy(&p);perror("maps");return 70;}if(rc<0)return 1;
 if(mode==2){p21_destroy(&p);p21_destroy(&p);rc=p21_create(&c,&p,&e);fprintf(stderr,"repeat stage=%s code=%d\n",e.stage,e.code);if(rc)return 2;}
 if(mode==3){char other[4096];snprintf(other,sizeof(other),"%s/smb.conf",argv[3]);c.config_file=other;mpv_handle *q=NULL;rc=p21_create(&c,&q,&e);fprintf(stderr,"conflict stage=%s code=%d\n",e.stage,e.code);if(q)p21_destroy(&q);rc=rc<0&&!strcmp(e.stage,"samba")&&e.code==EBUSY?0:3;}
 if(maps(argv[1]))rc=70;p21_destroy(&p);fprintf(stderr,"destroy complete result=%d\n",rc);return rc;
}
