#!/usr/bin/env python3
"""POSIX 8-bit RS-232 framing; custom rates are explicit, never approximated. MIT."""
import array,fcntl,struct,sys,termios

def configure(fd,baud=19200,parity='O',stop_bits=1,simulated=False):
    if not 75<=baud<=62400 or parity not in 'NOE' or stop_bits not in (1,2):
        raise ValueError('unsupported serial settings')
    attrs=termios.tcgetattr(fd)
    attrs[0]=termios.IGNPAR;attrs[1]=attrs[3]=0
    attrs[2]=termios.CS8|termios.CLOCAL|termios.CREAD
    if stop_bits==2:attrs[2]|=termios.CSTOPB
    if parity!='N' and not simulated:
        attrs[2]|=termios.PARENB
        if parity=='O':attrs[2]|=termios.PARODD
    speed=getattr(termios,'B'+str(baud),None)
    attrs[4]=attrs[5]=speed if speed is not None else baud if sys.platform=='darwin' and not simulated else termios.B38400
    attrs[6][termios.VMIN]=attrs[6][termios.VTIME]=0
    try:termios.tcsetattr(fd,termios.TCSANOW,attrs)
    except termios.error:
        if speed is not None or sys.platform!='darwin' or simulated:raise
        # Apple drivers may reject the custom integer here but accept it
        # through IOSSIOSPEED. The checked USB backend is applied afterward.
        attrs[4]=attrs[5]=termios.B38400
        termios.tcsetattr(fd,termios.TCSANOW,attrs)
    if speed is None and not simulated:
        if sys.platform=='darwin':
            fcntl.ioctl(fd,0x80085402,array.array('L',[baud])) # IOSSIOSPEED
        elif sys.platform.startswith('linux'):
            t=bytearray(44);fcntl.ioctl(fd,0x802c542a,t,True) # asm-generic termios2
            flags=struct.unpack_from('I',t,8)[0]
            struct.pack_into('I',t,8,(flags&~0x100f100f)|0x1000)
            struct.pack_into('II',t,36,baud,baud)
            fcntl.ioctl(fd,0x402c542b,t)
            fcntl.ioctl(fd,0x802c542a,t,True)
            if struct.unpack_from('II',t,36)!=(baud,baud):
                raise RuntimeError('serial driver rejected custom baud')
        else:raise RuntimeError('custom baud requires macOS or Linux')
    actual=termios.tcgetattr(fd)
    mask=termios.CSIZE|termios.PARENB|termios.PARODD|termios.CSTOPB|getattr(termios,'CRTSCTS',0)
    if actual[2]&mask!=attrs[2]&mask or (speed is not None and actual[4:6]!=attrs[4:6]):
        raise RuntimeError(f'serial driver did not apply {baud} 8{parity}{stop_bits}')
    return dict(baud=baud,parity=parity,stop_bits=stop_bits,simulated=simulated)
