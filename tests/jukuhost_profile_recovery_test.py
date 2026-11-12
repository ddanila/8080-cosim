#!/usr/bin/env python3
"""MIT. Shared recovery boundary: exact first frames, unknown state, cancellation."""
import json,os,pty,select,subprocess,sys,tempfile,time,tty
from pathlib import Path
from jukuhost_linux_pty_test import HOST,request,read_exact,wait_log
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'host/python'))
from jh_recovery import next_generation

HELPER='''import argparse,os,struct,time,termios
p=argparse.ArgumentParser();p.add_argument('--config');p.add_argument('--operation');p.add_argument('--serial-fd',type=int);p.add_argument('--result-fd',type=int);a,_=p.parse_known_args()
mode=open(a.config).read()
if a.operation=='prepare':
 attrs=termios.tcgetattr(a.serial_fd);attrs[4]=attrs[5]=termios.B19200;termios.tcsetattr(a.serial_fd,termios.TCSANOW,attrs)
if a.operation=='discover' and mode=='hang':
 open(a.config+'.pid','w').write(str(os.getpid()));time.sleep(60)
status=2 if a.operation=='discover' and mode=='uncertain' else 0
if a.operation=='discover' and mode=='disconnect':
 status=3;open(a.config,'w').write('unknown')
os.write(a.result_fd,b'JHR1'+bytes([status,ord('O'),1,0])+struct.pack('<II',19200,123))
'''

def main():
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);helper=root/'helper.py';helper.write_text(HELPER);config=root/'config';disk=root/'disk.img';disk.write_bytes(bytes(range(128))*6400)
  for mode in ['runtime','unknown','uncertain','disconnect','hang']:
   config.write_text(mode);master,slave=pty.openpty();tty.setraw(master);tty.setraw(slave)
   proc=subprocess.Popen([str(HOST),'--machine','kaypro2','--resume-disk','--recover-session','--serial',os.ttyname(slave),'--volume',str(disk),'--recovery-python',sys.executable,'--recovery-helper',str(helper),'--recovery-config',str(config)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   try:
    wait_log(proc,'phase=discover')
    if mode=='runtime':
     # Noise and signatures cannot hide a fragmented checked disk request.
     first=request(0x14,9,0,159,40);second=request(0x14,10,0,159,40)
     os.write(master,b'noise KP2 JB'+first[:3]);time.sleep(.02);os.write(master,first[3:]+second)
     response=read_exact(master,278)
     assert response[9:137]==bytes(range(128)) and response[148:276]==bytes(range(128))
     assert not Path(str(config)+'.pid').exists()
    elif mode=='unknown':
     assert not select.select([master],[],[],7)[0],'unknown state transmitted data'
     assert proc.poll() is None
    elif mode=='disconnect':
     wait_log(proc,'serial reconnected')
     wait_log(proc,'phase=discover')
     os.write(master,request(0x14,9,0,159,40));response=read_exact(master,139)
     assert response[9:137]==bytes(range(128))
    elif mode=='uncertain':
     assert proc.wait(timeout=8)==5
     assert not select.select([master],[],[],.1)[0]
    else:
     until=time.monotonic()+8
     while not Path(str(config)+'.pid').exists():
      assert time.monotonic()<until;time.sleep(.02)
     pid=int(Path(str(config)+'.pid').read_text());proc.terminate();proc.wait(timeout=3)
     try:os.kill(pid,0)
     except ProcessLookupError:pass
     else:raise AssertionError('helper survived cancellation')
   finally:
    if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
    proc.stdout.close();os.close(master);os.close(slave)
   print('PROFILE-RECOVERY',mode,'PASS',flush=True)
  a=root/'a';b=root/'b';a.mkdir();b.mkdir();registry=root/'registry'
  one=next_generation(a,registry);two=next_generation(b,registry);assert two==one+1
  (a/'generation.json').write_text('4294967295')
  try:next_generation(a,registry)
  except ValueError:pass
  else:raise AssertionError('generation wrapped')
 print('PROFILE-RECOVERY: PASS')
if __name__=='__main__':main()
