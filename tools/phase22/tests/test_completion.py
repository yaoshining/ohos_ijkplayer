from pathlib import Path
import unittest,tempfile,subprocess
R=Path(__file__).resolve().parents[1]
class Completion(unittest.TestCase):
 def test_ready_before_promise_continuation(self):
  source=(R/'app-native/napi.cpp').read_text();start=source.index('static void complete(');end=source.index('static std::string str(',start);fn=source[start:end]
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'test.cpp').write_text('''#include <atomic>
#include <string>
#include <cstdlib>
+using napi_env=int;using napi_status=int;using napi_value=int;using napi_deferred=int;using napi_async_work=int;
+#define NAPI_AUTO_LENGTH 0
+struct Job{int deferred,work;std::string result;};static std::atomic<bool>busy{true};
+void napi_create_string_utf8(int,const char*,int,int*){};void napi_delete_async_work(int,int){};
+void napi_resolve_deferred(int,int,int){if(busy)std::exit(77);busy=true;}
+'''.replace('\n+','\n')+fn+'int main(){complete(0,0,new Job{});return busy?0:78;}');subprocess.run(['c++','-std=c++17',str(p/'test.cpp'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
