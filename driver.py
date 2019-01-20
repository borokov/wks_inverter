import usb.core, usb.util, usb.control
import crc16
import datetime
import time

def getCommand(cmd):
    cmd = cmd.encode('utf-8')
    crc = crc16.crc16xmodem(cmd).to_bytes(2,'big')
    cmd = cmd+crc
    cmd = cmd+b'\r'
    while len(cmd)<8:
        cmd = cmd+b'\0'
    return cmd

def sendCommand(cmd):
    encodedCmd = getCommand(cmd)
    dev.ctrl_transfer(0x21, 0x9, 0x200, 0, encodedCmd)

def get_frame(timeout=100):
    values = ""
    ok = False
    while not ok:

        try:
            error = False
            res=""
            i=0
            while '\r' not in res and i<20:
                try:
                    res+="".join([chr(i) for i in dev.read(0x81, 8, timeout) if i!=0x00])
                except usb.core.USBError as e:
                    if e.errno == 110:
                        pass
                    else:
                        error = True
                i+=1

            crc = res[len(res)-3:-1]
            values = res[:-3]

            frame_crc_int = int.from_bytes([ord(crc[0]), ord(crc[1])], 'big')
            computed_crc_int = crc16.crc16xmodem(values.encode('utf-8'))

            if frame_crc_int != computed_crc_int:
                error = True

            if len(values) < 2:
                error = True

            if not error:
                print("ok")
                ok = True

        except Exception as e:
            print(repr(e))
        

    return values

class QPGS0(object):
    def __init__(self, frame):
        # ensure first '(' is removed
        if frame[0] == '(':
            frame = frame[1:]

        value_array = frame.split(' ')

        self.a = value_array[0]
        self.b = value_array[1]
        self.c = value_array[2]
        self.d = value_array[3]
        self.e_voltage_1 = value_array[4]
        self.f = value_array[5]
        self.g_voltage_2 = value_array[6]
        self.h_voltage_3 = value_array[7]
        self.i = value_array[8]
        self.j = value_array[9]
        self.k = value_array[10]
        self.l = value_array[11]
        self.m = value_array[12]
        self.o = value_array[14]
        self.p = value_array[15]
        self.q = value_array[16]
        self.r = value_array[17]
        self.s = value_array[18]
        self.t = value_array[19]
        self.u = value_array[20]
        self.v = value_array[21]
        self.w = value_array[22]
        self.x = value_array[23]
        self.y = value_array[24]
        self.z = value_array[25]
        self.z1 = value_array[26]

    def __str__(self):
        str = ""
        for member in sorted(self.__dict__):
            str += ("{}: {}\n".format(member, self.__dict__[member]))
        return str


vendorId = 0x0665
productId = 0x5161
interface = 0
print("Connecting USB - 1")
dev = usb.core.find(idVendor=vendorId, idProduct=productId)
print("Connecting USB - 2")
if dev.is_kernel_driver_active(interface):
    dev.detach_kernel_driver(interface)
print("Connecting USB - 3")
dev.set_interface_altsetting(0,0)

print("USB connected ---")


while True:
    sendCommand('QPGS0')
    res = get_frame()
    #print(res)
    print(QPGS0(res))
    t = datetime.datetime.now()
    #print("{}: {}".format(t,res))
