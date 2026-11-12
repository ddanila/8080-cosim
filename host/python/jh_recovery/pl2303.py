"""PL2303HXD endpoint-zero rate override; leaves Apple serial driver attached."""
import atexit,ctypes as c,struct,ctypes.util,plistlib,subprocess,sys

def device_identity(path):
 if sys.platform != "darwin":raise RuntimeError("PL2303 backend requires macOS")
 tree=plistlib.loads(subprocess.check_output(["ioreg","-a","-l","-r","-c","IOUSBHostDevice"]))
 def contains(node):
  return isinstance(node,dict) and (node.get("IOCalloutDevice")==path or any(contains(x) for x in node.get("IORegistryEntryChildren",[])))
 def devices(nodes):
  for node in nodes:
   if 'idVendor' in node and node.get('IOObjectClass')=='IOUSBHostDevice':yield node
   yield from devices(node.get('IORegistryEntryChildren',[]))
 matches=[x for x in devices(tree) if contains(x) and x.get('idVendor')==0x067b and x.get('idProduct')==0x2303]
 if len(matches)!=1:raise RuntimeError("Cannot uniquely map serial path to USB device")
 d=matches[0]
 if (d.get("idVendor"),d.get("idProduct"),d.get("bcdDevice"))!=(0x067b,0x2303,0x0400):raise RuntimeError("Adapter is not the qualified PL2303HXD revision")
 return {"path":path,"address":d["USB Address"],"location":d["locationID"],"revision":d["bcdDevice"]}

class USBRate:
 def __init__(self,path):
  self.identity=device_identity(path)
  u=self.u=c.CDLL(ctypes.util.find_library('usb-1.0') or '/opt/homebrew/lib/libusb-1.0.dylib')
  u.libusb_init.argtypes=[c.POINTER(c.c_void_p)];u.libusb_init.restype=c.c_int
  u.libusb_open_device_with_vid_pid.argtypes=[c.c_void_p,c.c_uint16,c.c_uint16];u.libusb_open_device_with_vid_pid.restype=c.c_void_p
  u.libusb_control_transfer.argtypes=[c.c_void_p,c.c_uint8,c.c_uint8,c.c_uint16,c.c_uint16,c.c_void_p,c.c_uint16,c.c_uint];u.libusb_control_transfer.restype=c.c_int
  u.libusb_close.argtypes=[c.c_void_p];u.libusb_exit.argtypes=[c.c_void_p]
  self.ctx=c.c_void_p();assert u.libusb_init(c.byref(self.ctx))==0
  u.libusb_get_device_list.argtypes=[c.c_void_p,c.POINTER(c.POINTER(c.c_void_p))];u.libusb_get_device_list.restype=c.c_ssize_t
  u.libusb_get_device_address.argtypes=[c.c_void_p];u.libusb_get_device_address.restype=c.c_uint8
  u.libusb_open.argtypes=[c.c_void_p,c.POINTER(c.c_void_p)]
  u.libusb_free_device_list.argtypes=[c.POINTER(c.c_void_p),c.c_int]
  devices=c.POINTER(c.c_void_p)();count=u.libusb_get_device_list(self.ctx,c.byref(devices))
  candidates=[devices[i] for i in range(max(0,count)) if u.libusb_get_device_address(devices[i])==self.identity['address']]
  self.h=c.c_void_p()
  try:
   if len(candidates)!=1:raise RuntimeError('USB address is ambiguous; refusing to select another adapter')
   if u.libusb_open(candidates[0],c.byref(self.h))!=0:raise RuntimeError('Cannot open selected USB adapter')
  finally:u.libusb_free_device_list(devices,1)
  if not self.h:raise RuntimeError('Cannot open PL2303 device')
  atexit.register(self.close)
 def close(self):
  if self.h:self.u.libusb_close(self.h);self.h=None;self.u.libusb_exit(self.ctx)
 def get(self):
  b=(c.c_ubyte*7)();r=self.u.libusb_control_transfer(self.h,0xa1,0x21,0,0,b,7,1000)
  if r!=7:raise RuntimeError(f'GET_LINE_CODING failed {r}')
  return bytes(b)
 def set(self,rate,parity=1,stop_bits=1):
  if not 75<=rate<=62400 or parity not in (0,1,2) or stop_bits not in (1,2):raise ValueError("unsupported line settings")
  if rate==9600:encoded=struct.pack('<I',rate);actual=rate
  else:
   mantissa=384000000//rate;exponent=0
   while mantissa>=512:
    mantissa>>=2;exponent+=1
   assert 1<=mantissa<=511 and exponent<=7
   encoded=bytes([mantissa&255,(exponent<<1)|(mantissa>>8),0,0x80])
   actual=(384000000//mantissa)>>(exponent*2)
  # Explicit framing: USB CDC parity 1 = odd, 0 = none.
  coding=encoded+bytes([0 if stop_bits==1 else 2,parity,8])
  b=(c.c_ubyte*7).from_buffer_copy(coding)
  r=self.u.libusb_control_transfer(self.h,0x21,0x20,0,0,b,7,1000)
  if r!=7:raise RuntimeError(f'SET_LINE_CODING failed {r}')
  readback=self.get()
  if readback!=coding:raise RuntimeError(f'line coding mismatch {readback.hex()} != {coding.hex()}')
  return {'requested':rate,'calculated_actual':actual,'coding':coding.hex(),'error_percent':100*(actual/rate-1),'device':self.identity}
