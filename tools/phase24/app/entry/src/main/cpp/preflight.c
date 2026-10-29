#define _GNU_SOURCE
#include "integration.h"
#include <libavutil/sha.h>
#include <libavutil/mem.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
static int check(const char *p,int directory,int writable) {
 char real[4096];struct stat st;
 if(!p||p[0]!='/'||strlen(p)>4095){errno=EINVAL;return -1;}
 for(const unsigned char *s=(const unsigned char*)p;*s;s++)if(*s<32||*s==127||*s=='%'){errno=EINVAL;return -1;}
 if(!realpath(p,real))return -1;
 if(strcmp(p,real)){errno=EINVAL;return -1;}
 if(stat(p,&st))return -1;
 if(directory?!S_ISDIR(st.st_mode):!S_ISREG(st.st_mode)){errno=directory?ENOTDIR:EINVAL;return -1;}
 int mask=directory?(R_OK|X_OK):R_OK;
 if(writable)mask|=W_OK;
 if(!(st.st_mode&0444)||(directory&&!(st.st_mode&0111))||(writable&&!(st.st_mode&0222))){errno=EACCES;return -1;}
 return faccessat(AT_FDCWD,p,mask,AT_EACCESS);
}
static int child(char *p,const char *root,const char *suffix) {
 int n=snprintf(p,4096,"%s/%s",root,suffix);if(n<0||n>=4096){errno=ENAMETOOLONG;return -1;}return 0;
}
int p21_validate(const struct p21_config *c,struct p21_error *e) {
 char path[4096],fonts[4096];FILE *f=NULL;struct AVSHA *sha=NULL;DIR *dir=NULL;int saved;
 e->stage="resources";
 if(!c){errno=EINVAL;goto fail;}
 if(check(c->config_file,0,0)||check(c->state_root,1,1)||check(c->cache_root,1,1)||check(c->resource_root,1,0))goto fail;
 const char *subs[]={"private","state","lock"};
 for(size_t i=0;i<3;i++)if(child(path,c->state_root,subs[i])||check(path,1,1))goto fail;
 if(child(path,c->cache_root,"demux")||check(path,1,1))goto fail;
 if(child(fonts,c->resource_root,"fonts")||check(fonts,1,0))goto fail;
 if(child(path,fonts,"font1.ttf")||check(path,0,0))goto fail;
 dir=opendir(fonts);if(!dir)goto fail;
 struct dirent *de;
 while((de=readdir(dir)))if(strcmp(de->d_name,".")&&strcmp(de->d_name,"..")&&strcmp(de->d_name,"font1.ttf")){errno=EINVAL;goto fail;}
 closedir(dir);dir=NULL;
 f=fopen(path,"rb");if(!f)goto fail;
 sha=av_sha_alloc();if(!sha){errno=ENOMEM;goto fail;}av_sha_init(sha,256);
 unsigned char buf[4096],sum[32];size_t n,total=0;
 while((n=fread(buf,1,sizeof(buf),f))){total+=n;if(total>16744){errno=EINVAL;goto fail;}av_sha_update(sha,buf,n);}
 if(ferror(f)){errno=EIO;goto fail;}
 av_sha_final(sha,sum);char hex[65];for(int i=0;i<32;i++)snprintf(hex+i*2,3,"%02x",sum[i]);
 if(total!=16744||strcmp(hex,"7b8a5f6cfd5fdb06ddac7d976935babf05afa5ef7bf6b8c1b8cf919b481d33e1")){errno=EINVAL;goto fail;}
 fclose(f);av_free(sha);e->code=0;return 0;
fail:
 saved=errno;if(dir)closedir(dir);if(f)fclose(f);av_free(sha);e->code=saved;return -1;
}
