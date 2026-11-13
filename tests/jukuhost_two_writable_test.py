#!/usr/bin/env python3
"""Two writable raw Kaypro images, drive isolation, replay and both journals."""
import os,pty,tty,tempfile,subprocess,signal,fcntl
from pathlib import Path
from jukuhost_linux_pty_test import HOST,request,read_exact,wait_log,journal,NATIVE_BYTES

def main():
 with tempfile.TemporaryDirectory() as name:
  root=Path(name);a=root/'a.img';b=root/'b.img'
  a.write_bytes(bytes(NATIVE_BYTES));b.write_bytes(bytes([0x22])*NATIVE_BYTES)
  master,slave=pty.openpty();cm,cs=pty.openpty()
  for fd in [master,slave,cm,cs]:tty.setraw(fd)
  base=[str(HOST),'--machine','kaypro2','--serial',os.ttyname(slave),'--resume-disk','--volume',str(a),'--drive-b',str(b),'--console-pty',os.ttyname(cs),'--disk-baud','19200','--writable']
  def start(extra):
   p=subprocess.Popen(base+extra,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   wait_log(p,'serving A:');return p
  def stop(p):p.send_signal(signal.SIGINT);p.wait(timeout=5);assert p.returncode==0
  p=None
  try:
   p=start(['--drive-b-writable'])
   for path in (a,b):
    with path.open('r+b') as f:
     try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
     except BlockingIOError:pass
     else:raise AssertionError('active writable media was not locked')
   for drive in (0,1):
    payload=bytes([0xa0+drive])*128
    pkt=request(0x15,drive+1,drive,3,2,payload);os.write(master,pkt)
    reply=read_exact(master,7);assert reply[3:5]==b'\0\0'
    os.write(master,pkt);assert read_exact(master,7)==reply
    image=[a,b][drive].read_bytes();assert image[3*5120+128:3*5120+256]==payload
   stop(p);p=None
   for drive,path in enumerate([a,b]):
    image=bytearray(path.read_bytes());before=image[:128];after=bytes([0xf0+drive])*128
    image[:128]=after;path.write_bytes(image)
    Path(str(path)+'.jhj').write_bytes(journal(2,90+drive,0,before,after))
   p=start(['--drive-b-writable'])
   assert a.read_bytes()[:128]==bytes(128) and b.read_bytes()[:128]==bytes([0x22])*128
   assert not Path(str(a)+'.jhj').exists() and not Path(str(b)+'.jhj').exists()
   stop(p);p=None
   p=start([])
   before=b.read_bytes();os.write(master,request(0x15,9,1,3,2,bytes(128)))
   reply=read_exact(master,7);assert reply[3]!=0 and b.read_bytes()==before,reply.hex()
   # Read-only Kaypro B uses the same raw order as writable B.
   os.write(master,request(0x11,10,1,3,2));reply=read_exact(master,133)
   assert reply[4:-1]==bytes([0xa1])*128
   stop(p);p=None
   before=b.read_bytes();Path(str(b)+'.jhj').write_bytes(b'bad journal')
   bad=subprocess.run(base+['--drive-b-writable'],capture_output=True,timeout=5)
   assert bad.returncode==6 and b.read_bytes()==before
  finally:
   if p is not None and p.poll() is None:p.kill();p.wait()
   for fd in [master,slave,cm,cs]:os.close(fd)
 print('TWO-WRITABLE: PASS (A/B isolation, duplicate writes, both journals, read-only B, raw geometry, locking, malformed journal rejection)')
if __name__=='__main__':main()
