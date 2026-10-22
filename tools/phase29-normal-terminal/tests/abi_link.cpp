#include <mpv/ohcodec_terminal.h>
int main(){mpv_ohcodec_terminal_record r={0};r.size=sizeof(r);r.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION;return mpv_ohcodec_terminal_api_version()==MPV_OHCODEC_TERMINAL_ABI_VERSION && mpv_ohcodec_terminal_snapshot(&r)==0?0:1;}
