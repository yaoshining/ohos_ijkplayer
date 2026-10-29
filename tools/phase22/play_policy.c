#include <stdint.h>
#include <stdlib.h>
#include <errno.h>
int p22_surface_valid(const char *s,int w,int h){if(!s||!*s||w<=0||h<=0||w>16384||h>16384)return 0;for(const char *p=s;*p;p++)if(*p<'0'||*p>'9')return 0;errno=0;char *end;unsigned long long n=strtoull(s,&end,10);return !errno&&!*end&&n>0;}
