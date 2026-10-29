from pathlib import Path
import hashlib,zipfile,io,struct,json,subprocess

def verified_binary(raw,lock):
 if hashlib.sha256(raw).hexdigest()!=lock['archiveSHA256']:raise ValueError('Ninja archive digest mismatch')
 with zipfile.ZipFile(io.BytesIO(raw))as z:
  if z.namelist()!=['ninja']:raise ValueError('unexpected Ninja archive files')
  data=z.read('ninja')
 if hashlib.sha256(data).hexdigest()!=lock['binarySHA256']:raise ValueError('Ninja binary digest mismatch')
 if len(data)<20 or data[:7]!=b'\x7fELF\x02\x01\x01' or struct.unpack_from('<H',data,18)[0]!=62:raise ValueError('Ninja must be Linux x86_64 ELF')
 return data

def main():
 here=Path(__file__).resolve().parent;repo=here.parents[1];dest=repo/'out/phase17-host-tools';dest.mkdir(parents=True,exist_ok=False);lock=json.loads((here/'ninja-lock.json').read_text());archive=dest/'ninja-linux.zip'
 subprocess.run(['curl','--http1.1','-fL','--retry','3','--connect-timeout','20','--max-time','120',lock['url'],'-o',str(archive)],check=True)
 binary=dest/'ninja';binary.write_bytes(verified_binary(archive.read_bytes(),lock));binary.chmod(0o755)
 version=subprocess.check_output([str(binary),'--version'],text=True).strip()
 if version!=lock['version']:raise ValueError('Ninja runtime version mismatch')
 (dest/'binding.json').write_text(json.dumps({**lock,'verifiedRuntimeVersion':version},indent=2)+'\n')
 print('Verified official Linux Ninja',version)
if __name__=='__main__':main()
