import re

def completed(mode,result_command,run_log):
 return bool(result_command.get('exit')==0 and not result_command.get('timeout') and re.search(r'loaded=\d+ eof=\d+ errors=\d+',result_command.get('stdout','')) and 'P24_BEGIN case='+mode+' ' in run_log and 'P24_RESULT '+result_command.get('stdout','').strip() in run_log)
