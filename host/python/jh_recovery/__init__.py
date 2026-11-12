"""MIT. Shared launch contract for native-host recovery profiles."""
import fcntl
import secrets
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def atomic_json(path, value):
    path=Path(path);temporary=path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def arguments(host, session, driver, settings, artifacts, **options):
    """Caller holds the session lock. Freeze identities before touching serial."""
    host=Path(host).resolve();session=Path(session).resolve()
    root=Path(__file__).resolve().parent
    bound={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in artifacts}
    for path in [host,*root.glob('*.py'),*Path(driver).parent.glob('*.py')]:
        bound[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
    config=dict(schema=1,driver=str(Path(driver).resolve()),session=str(session),
        settings=settings,artifacts=bound,**options)
    path=session/'recovery.json'
    if path.exists():
        previous=json.loads(path.read_text())
        if previous.get('adapter_identity'):config['adapter_identity']=previous['adapter_identity']
    atomic_json(path,config)
    return ['--recover-session','--recovery-python',sys.executable,
        '--recovery-helper',str(root/'helper.py'),'--recovery-config',str(path)]

def next_generation(session, registry=None):
    """Caller holds session.lock; a global lock prevents cross-session reuse.

    A copied session advances past its last epoch too. The initial random
    namespace reduces collisions with independently operated host computers;
    these 32-bit protocol epochs are not cryptographic identities.
    """
    path=session/'generation.json'
    registry=Path(registry) if registry is not None else Path.home()/'.cache/jukuhost'
    registry.mkdir(parents=True,exist_ok=True)
    def write(target,value):
        temporary=target.with_suffix('.tmp')
        with temporary.open('w') as stream:
            stream.write(json.dumps(value)+'\n');stream.flush();os.fsync(stream.fileno())
        temporary.replace(target)
    with (registry/'generation.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        global_path=registry/'generation.json'
        global_value=json.loads(global_path.read_text()) if global_path.exists() else secrets.randbits(31)
        local_value=json.loads(path.read_text()) if path.exists() else 0
        value=max(global_value,local_value)+1
        if not 1<=value<=0xffffffff:raise ValueError('session generation exhausted')
        write(global_path,value);write(path,value)
    return value


def configure_link(fd,path,baud,parity='N',stop_bits=1,adapter='posix'):
    from .serial_format import configure
    from .pl2303 import USBRate
    simulated=os.ttyname(fd).startswith(('/dev/pts/','/dev/ttys','/dev/pty'))
    result=configure(fd,baud,parity,stop_bits,simulated)
    if adapter=='pl2303hxd' and not simulated:
        usb=USBRate(path)
        try:result['usb']=usb.set(baud,parity={'N':0,'O':1,'E':2}[parity],stop_bits=stop_bits)
        finally:usb.close()
    return result


def preflight(host):
    import subprocess
    result=subprocess.run([str(Path(host).resolve()),'--recovery-python',sys.executable,
        '--recovery-helper',str(Path(__file__).with_name('helper.py')),
        '--recovery-config','preflight-only','--help'],capture_output=True,text=True,timeout=5)
    if result.returncode:raise ValueError('host lacks shared recovery support; rebuild the pinned host')


def run_child(command,fd):
    """Keep descriptor ownership in the launcher and forward termination."""
    import signal,subprocess
    child=None
    def stop(signum,frame):raise KeyboardInterrupt
    previous=signal.signal(signal.SIGTERM,stop)
    try:
        child=subprocess.Popen(command,pass_fds=(fd,))
        try:return child.wait()
        except KeyboardInterrupt:return 130
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        signal.signal(signal.SIGTERM,previous)
