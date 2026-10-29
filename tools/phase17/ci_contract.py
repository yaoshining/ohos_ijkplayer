"""Validate reported scope; external run/commit and downloaded bytes need independent binding."""
import re
from pathlib import PurePosixPath
def validate_claim(report):
 if report.get('coverage')!='actual-cross-build':raise ValueError('not an actual cross build')
 if not re.fullmatch(r'[0-9a-f]{40}',report.get('commit','')):raise ValueError('missing fixed commit')
 if not re.fullmatch(r'https://github.com/yaoshining/ohos_ijkplayer/actions/runs/[0-9]+',report.get('runUrl','')):raise ValueError('missing run identity')
 if not report.get('platform')or not report.get('runner'):raise ValueError('missing platform')
 runs=report.get('runs',[])
 if len(runs)!=2 or len({r.get('root')for r in runs})!=2:raise ValueError('need two distinct runs')
 for row in runs:
  if row.get('fresh')is not True or not PurePosixPath(row.get('root','')).is_absolute():raise ValueError('not a fresh absolute root')
  if not re.fullmatch(r'[0-9a-f]{64}',row.get('artifactSha256','')):raise ValueError('artifact digest missing')
  for step in ['libplacebo-build','libplacebo-install','mpv-build','mpv-install','mpv-strip','static-validation']:
   if row.get('steps',{}).get(step)!=0:raise ValueError('missing or failed step: '+step)
 if report.get('comparisonPassed')is not True or runs[0]['artifactSha256']!=runs[1]['artifactSha256']:raise ValueError('repro not passed')
 return True
