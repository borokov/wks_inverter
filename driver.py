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

def getResult(timeout=100):
    res=""
    i=0
    error = False
    while '\r' not in res and i<20:
        try:
            res+="".join([chr(i) for i in dev.read(0x81, 8, timeout) if i!=0x00])
        except usb.core.USBError as e:
            if e.errno == 110:
                error = True
                pass
            else:
                print("fatal error")
                raise
        i+=1

    if error:
        return "error"

    crc = res[len(res)-3:-1]
    values = res[:-3]

    frame_crc_int = int.from_bytes([ord(crc[0]), ord(crc[1])], 'big')
    computed_crc_int = crc16.crc16xmodem(values.encode('utf-8'))

    if frame_crc_int != computed_crc_int:
        return "Invalid CRC"

    return values



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

#command = getCommand('QPI')
#sendCommand(command)
#res = getResult()
#print(res)
#
#command = getCommand('QGMN')
#sendCommand(command)
#res = getResult()
#print(res)
#
#command = getCommand('QPI')
#sendCommand(command)
#res = getResult()
#print(res)
#
#command = getCommand('QGMN')
#sendCommand(command)
#res = getResult()
#print(res)
#

while True:
    sendCommand('QPGS0')
    res = getResult()
    t = datetime.datetime.now()
    print("{}: {}".format(t,res))
    time.sleep(1)
