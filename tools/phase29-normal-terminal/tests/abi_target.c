#include <mpv/ohcodec_terminal.h>
/* ARM64 C/C++链接探针，只链接不执行；强引用全部四个扩展入口。 */
int main(void) {
    mpv_ohcodec_terminal_record r={0};
    r.size=sizeof(r);r.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION;
    int registration=mpv_ohcodec_terminal_register(0);
    int enabled=mpv_ohcodec_terminal_enable();
    return mpv_ohcodec_terminal_api_version()==MPV_OHCODEC_TERMINAL_ABI_VERSION &&
        registration<0 && enabled<0 && mpv_ohcodec_terminal_snapshot(&r)==0 ? 0:1;
}
