#!/usr/bin/env python3
"""MIT. One supervised profile operation; never starts a disk server."""
import errno
import argparse,hashlib,importlib.util,json,os,select,struct,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from jh_recovery import atomic_json,next_generation
from jh_recovery.serial_format import configure
from jh_recovery.pl2303 import USBRate

class Port:
    def __init__(self,fd,config):
        self.fd=fd;self.config=config
        self.simulated=os.ttyname(fd).startswith(('/dev/pts/','/dev/ttys','/dev/pty'))
        self.settings=dict(config['settings'])
        self.usb=USBRate(config['serial']) if config.get('adapter')=='pl2303hxd' and not self.simulated else None
        if self.usb:
            stable={key:self.usb.identity[key] for key in ('path','location','revision')}
            if config.get('adapter_identity',stable)!=stable:
                self.usb.close();raise ValueError('configured USB adapter identity changed')
            config['adapter_identity']=stable
    def apply(self,baud,parity,stop_bits=1):
        self.settings=configure(self.fd,baud,parity,stop_bits,self.simulated)
        if self.usb:self.settings['usb']=self.usb.set(baud,parity={'N':0,'O':1,'E':2}[parity],stop_bits=stop_bits)
        return self.settings
    def read(self,size,timeout):
        if not select.select([self.fd],[],[],max(0,timeout))[0]:return b''
        data=os.read(self.fd,size)
        if not data:raise ConnectionError('serial disconnected')
        return data
    def write(self,data):
        end=time.monotonic()+5;data=memoryview(data)
        while data:
            if not select.select([],[self.fd],[],max(0,end-time.monotonic()))[1]:raise TimeoutError('write timeout')
            try:count=os.write(self.fd,data)
            except BlockingIOError:continue
            if not count:raise ConnectionError('short serial write')
            data=data[count:]
    def close(self):
        if self.usb:self.usb.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--operation',choices=['prepare','discover'],required=True);p.add_argument('--current-baud',type=int);p.add_argument('--current-parity');p.add_argument('--current-stops',type=int);p.add_argument('--config',type=Path,required=True);p.add_argument('--serial-fd',type=int,required=True);p.add_argument('--result-fd',type=int,required=True);a=p.parse_args()
    config=json.loads(a.config.read_text());report=dict(schema=1,status='intervention-required',operation=a.operation);port=None
    try:
        if config['schema']!=1:raise ValueError('unsupported recovery configuration')
        for path,digest in config['artifacts'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('recovery artifact changed: '+path)
        sys.path.insert(0,str(Path(config['driver']).parent))
        spec=importlib.util.spec_from_file_location('machine_recovery',config['driver']);driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        port=Port(a.serial_fd,config)
        if a.operation=='prepare':
            desired=config['settings']
            if (a.current_baud,a.current_parity,a.current_stops)!=(desired['baud'],desired['parity'],desired['stop_bits']):
                port.apply(desired['baud'],desired['parity'],desired['stop_bits'])
            report.update(status='unknown')
        else:report.update(driver.recover(port,config))
        if report['status'] not in ('unknown','booted'):raise ValueError('invalid profile result')
        if report.get('rom'):config['last_rom']=report['rom']
        if config.get('last_rom'):report['last_rom']=config['last_rom']
        settings=port.settings
        report['settings']=settings
        atomic_json(Path(config['session'])/'recovery-state.json',report)
        config['settings']=settings;atomic_json(a.config,config)
        os.write(a.result_fd,b'JHR1'+bytes([int(report['status']=='booted'),ord(settings['parity']),settings['stop_bits'],0])+struct.pack('<II',settings['baud'],next_generation(Path(config['session']))))
    except OSError as error:
        report['error']=str(error)
        if not isinstance(error,ConnectionError) and error.errno not in (errno.EIO,errno.ENODEV,errno.ENXIO,errno.EBADF,errno.EPIPE,errno.ECONNRESET,errno.ENOTCONN):
            traceback.print_exc();return 1
        report['status']='disconnected'
        settings=port.settings if port else config['settings']
        os.write(a.result_fd,b'JHR1'+bytes([3,ord(settings['parity']),settings['stop_bits'],0])+struct.pack('<II',settings['baud'],0))
        return 0
    except Exception as error:
        report['error']=str(error);traceback.print_exc()
        atomic_json(Path(config['session'])/'recovery-state.json',report)
        return 1
    finally:
        if port:port.close()
        atomic_json(Path(config['session'])/('recovery-'+str(time.time_ns())+'.json'),report)
    return 0
if __name__=='__main__':sys.exit(main())
