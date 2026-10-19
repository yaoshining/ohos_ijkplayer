"""Apply the explicit runtime contract only inside a fresh diagnostic source tree."""
from pathlib import Path
import argparse,hashlib,json,shutil,difflib
HERE=Path(__file__).resolve().parent
SAMBA_FILES=['dynconfig/dynconfig.c','source3/libsmb/libsmb_context.c','source3/libsmb/libsmb_setget.c','source3/param/loadparm.c','source3/lib/gencache.c']
FFMPEG_FILES=['libavformat/libsmbclient.c','libavformat/Makefile','libavformat/libavformat.v']
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('expected one original source anchor: '+repr(a[:80]))
 return s.replace(a,b,1)
def samba(root):
 root=Path(root);original={n:(root/n).read_text() for n in SAMBA_FILES};updated=dict(original)
 if (root/'dynconfig/smb_runtime.c').exists():raise ValueError('runtime patch already applied')
 s=original['dynconfig/dynconfig.c'];s=once(s,'#include "dynconfig.h"','#include "dynconfig.h"\n#include "smb_runtime_internal.h"')
 s=once(s,'const char *get_dyn_##name(void) \\\n{\\\n\treturn dyn_##name;\\\n}', 'const char *get_dyn_##name(void) \\\n{\\\n\tconst char *runtime = rt_dyn(#name);\\\n\treturn runtime ? runtime : dyn_##name;\\\n}')
 updated['dynconfig/dynconfig.c']=s+'\n#include "smb_runtime.c"\n'
 s=original['source3/libsmb/libsmb_context.c'];s=once(s,'#include "includes.h"','#include "includes.h"\n#include "../../dynconfig/smb_runtime_internal.h"')
 s=once(s,'static bool SMBC_initialized = false;', '''static bool SMBC_initialized = false;
static int rt_module_error;
static bool rt_apply_paths(void)
{
    const char *names[] = {"private dir", "state directory", "lock directory", "cache directory", "pid directory", "smb passwd file"};
    for (size_t i=0; i<sizeof(names)/sizeof(names[0]); i++) {
        if (!lp_do_parameter(-1, names[i], rt_parameter(names[i]))) return false;
    }
    return strcmp(lp_private_dir(), rt_dyn("PRIVATE_DIR")) == 0 &&
           strcmp(lp_state_directory(), rt_dyn("STATEDIR")) == 0 &&
           strcmp(lp_lock_directory(), rt_dyn("LOCKDIR")) == 0 &&
           strcmp(lp_cache_directory(), rt_dyn("CACHEDIR")) == 0 &&
           strcmp(lp_pid_directory(), rt_dyn("PIDDIR")) == 0 &&
           strcmp(lp_smb_passwd_file(), rt_dyn("SMB_PASSWD_FILE")) == 0;
}''')
 start=s.index('\thome = getenv("HOME");');end=s.index('\n\tload_interfaces();',start)
 legacy=s[start:end];explicit='''\tif (rt_dyn("CONFIGFILE")) {
        if (rt_validate_current() || !lp_load_client(rt_dyn("CONFIGFILE")) || !rt_apply_paths()) {
            rt_module_error = EIO;
            rt_fail();
            TALLOC_FREE(frame);
            return;
        }
    } else {
'''+legacy+'\n    }\n'
 s=s[:start]+explicit+s[end:]
 s=once(s,'SMBCCTX *\nsmbc_new_context(void)','static SMBCCTX *\nsmbc_new_context_runtime_original(void)')
 s=once(s,'SMB_THREAD_ONCE(&SMBC_initialized, SMBC_module_init, NULL);','''if (!SMBC_initialized) {
            rt_module_error = 0;
            SMBC_module_init(NULL);
            if (rt_module_error) {
                SMBC_module_terminate();
                TALLOC_FREE(frame);
                errno = rt_module_error;
                return NULL;
            }
            SMBC_initialized = true;
        }''')
 s=once(s,'int\nsmbc_free_context(SMBCCTX *context,','static int\nsmbc_free_context_runtime_original(SMBCCTX *context,')
 s=once(s,'        /* Things we have to clean up */','        bool runtime_was_initialized = context->internal->initialized;\n        /* Things we have to clean up */')
 s=once(s,'if (initialized_ctx_count) {','if (runtime_was_initialized && initialized_ctx_count) {')
 s=once(s,'\tif (initialized_ctx_count == 0) {\n            SMBC_module_terminate();\n\t}', '/* Global teardown is performed by the wrapper after ALL allocated contexts are freed. */')
 s=once(s,'SMBCCTX *\nsmbc_init_context(SMBCCTX *context)','static SMBCCTX *\nsmbc_init_context_runtime_original(SMBCCTX *context)')
 updated['source3/libsmb/libsmb_context.c']=s+'\n#include "../../dynconfig/smb_context_wrappers.inc"\n'
 s=original['source3/libsmb/libsmb_setget.c'];s=once(s,'#include "includes.h"','#include "includes.h"\n#include "../../dynconfig/smb_runtime_internal.h"')
 s=once(s,'int smbc_setConfiguration(SMBCCTX *c, const char *file)','static int smbc_setConfiguration_runtime_original(SMBCCTX *c, const char *file)')
 s+='''\nint smbc_setConfiguration(SMBCCTX *c, const char *file)
{
    int result, saved;
    if (rt_lock()) return -1;
    if (rt_dyn("CONFIGFILE")) { rt_unlock(); errno=EBUSY; return -1; }
    if (rt_begin()) { rt_unlock(); return -1; }
    result=smbc_setConfiguration_runtime_original(c,file);
    saved=errno; rt_unlock(); errno=saved; return result;
}
''';updated['source3/libsmb/libsmb_setget.c']=s
 s=original['source3/param/loadparm.c'];s=once(s,'#include "includes.h"','#include "includes.h"\n#include "../../dynconfig/smb_runtime_internal.h"')
 helper='''static const char *rt_loadparm_value(const char *name, const char *value)
{
    const char *names[] = {"private dir", "state directory", "lock directory", "cache directory", "pid directory", "smb passwd file"};
    int id = lpcfg_map_parameter(name);
    if (id < 0 || !rt_dyn("CONFIGFILE")) return value;
    for (size_t i=0; i<sizeof(names)/sizeof(names[0]); i++) {
        int canonical=lpcfg_map_parameter(names[i]);
        if (canonical >= 0 && parm_table[id].offset == parm_table[canonical].offset &&
            parm_table[id].p_class == parm_table[canonical].p_class)
            return rt_parameter(names[i]);
    }
    return value;
}

'''
 s=once(s,'bool lp_do_parameter(int snum, const char *pszParmName, const char *pszParmValue)',helper+'bool lp_do_parameter(int snum, const char *pszParmName, const char *pszParmValue)')
 s=once(s,'\tlp_ctx = setup_lp_context(frame);\n\tif (lp_ctx == NULL) {','\tpszParmValue = rt_loadparm_value(pszParmName, pszParmValue);\n\tlp_ctx = setup_lp_context(frame);\n\tif (lp_ctx == NULL) {')
 anchor='static bool do_parameter(const char *pszParmName, const char *pszParmValue,\n\t\t\t void *userdata)\n{'
 s=once(s,anchor,anchor+'\n\tpszParmValue = rt_loadparm_value(pszParmName, pszParmValue);')
 updated['source3/param/loadparm.c']=s
 s=original['source3/lib/gencache.c'];s=once(s,'#include "includes.h"','#include "includes.h"\n#include "../../dynconfig/smb_runtime_internal.h"')
 s=once(s,'if (cache == NULL && errno == EACCES && geteuid() != 0)', 'if (!rt_dyn("CONFIGFILE") && cache == NULL && errno == EACCES && geteuid() != 0)');updated['source3/lib/gencache.c']=s
 for n,s in updated.items():(root/n).write_text(s)
 for p in (HERE/'runtime').iterdir():shutil.copyfile(p,root/'dynconfig'/p.name)
 return evidence(root,original,updated)
def ffmpeg(root):
 root=Path(root);original={n:(root/n).read_text() for n in FFMPEG_FILES};updated=dict(original)
 if (root/'libavformat/ohcodec_smb_runtime.h').exists():raise ValueError('runtime patch already applied')
 updated['libavformat/libsmbclient.c']+='''\n#include "ohcodec_smb_runtime.h"
extern int ohcodec_smb_runtime_configure_internal(const struct ohcodec_smb_runtime_v1 *);
int ohcodec_smb_runtime_configure_v1(const struct ohcodec_smb_runtime_v1 *config)
{
    return ohcodec_smb_runtime_configure_internal(config);
}
'''
 updated['libavformat/Makefile']=once(updated['libavformat/Makefile'],'HEADERS = avformat.h','HEADERS = ohcodec_smb_runtime.h \\\n          avformat.h')
 updated['libavformat/libavformat.v']=once(updated['libavformat/libavformat.v'],'        av*;','        av*;\n        ohcodec_smb_runtime_configure_v1;')
 for n,s in updated.items():(root/n).write_text(s)
 shutil.copyfile(HERE/'runtime/smb_runtime.h',root/'libavformat/ohcodec_smb_runtime.h')
 return evidence(root,original,updated)
def evidence(root,original,updated):
 result={'files':[],'patch':''}
 for n,s in updated.items():
  result['files'].append({'path':n,'beforeSHA256':hashlib.sha256(original[n].encode()).hexdigest(),'afterSHA256':hashlib.sha256(s.encode()).hexdigest()})
  result['patch']+=''.join(difflib.unified_diff(original[n].splitlines(True),s.splitlines(True),fromfile='a/'+n,tofile='b/'+n))
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('kind',choices=['samba','ffmpeg']);a.add_argument('source',type=Path);a.add_argument('--evidence',required=True,type=Path);v=a.parse_args();d=globals()[v.kind](v.source);v.evidence.write_text(json.dumps(d,indent=2)+'\n')
