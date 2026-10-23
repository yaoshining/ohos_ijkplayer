#include <string.h>
int p22_mode(const char *s){if(!s)return 0;const char *m[]={"init","repeat","conflict"};for(int i=0;i<3;i++)if(!strcmp(s,m[i]))return i+1;return 0;}
