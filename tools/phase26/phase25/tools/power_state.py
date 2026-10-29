import re
def parse_power(text):
    match=re.search(r'^Current State:\s*([A-Z_]+)\b',text,re.M)
    return match.group(1) if match else 'unknown'
