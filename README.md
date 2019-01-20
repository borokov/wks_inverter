# Reverse ingeneering protocole #

Hightly inspired by http://allican.be/blog/2017/01/28/reverse-engineering-cypress-serial-usb.html

## Capturing trace ##

Using USBPcap: https://desowin.org/usbpcap/tour.html
Generate an xxx.pcap that can be open with wireshark: https://www.wireshark.org/

watchpower_trace.pcap has been generating before starting watchpower. One can see initialisation at the begining of trace follow by streamed data.

## Simulate trace on Raspberry Pi ##

I have an old Raspberry Pi 1 model B+ (I think...). I just installed rasbpbian on it, activate ssh and plug it into inverter USB out.

```lsusb``` gave me this:

```console
Bus 001 Device 005: ID 050d:1102 Belkin Components F7D1102 N150/Surf Micro Wireless Adapter v1000 [Realtek RTL8188CUS]
Bus 001 Device 004: ID 0665:5161 Cypress Semiconductor USB to Serial
Bus 001 Device 003: ID 0424:ec00 Standard Microsystems Corp. SMSC9512/9514 Fast Ethernet Adapter
Bus 001 Device 002: ID 0424:9512 Standard Microsystems Corp. SMC9512/9514 USB Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

One can see on line 2
```console
Bus 001 Device 004: ID 0665:5161 Cypress Semiconductor USB to Serial
```

Seems good. Device is recognized by the system. I hate spending time installing driver to make this damn penguin recongnizing hardware. ANyway, we can note vendor and product ids:

```
vendor: 0x0665
product: 0x5161
```
and give it to our python usb driver. Here I had an error "Access denied ...". After some reasearch, I end up with:

```console
sudo chmod 777 /dev/bus/usb/001/004
```

where 001 and 004 are Bus and Device given by lsusb. I know, there is probably better to handle this but it works and OS configuration is learly not the fun part here. I finally manage to make the small script below working:

```python
import usb.core, usb.util, usb.control
import crc16

def getCommand(cmd):
    cmd = cmd.encode('utf-8')
    crc = crc16.crc16xmodem(cmd).to_bytes(2,'big')
    cmd = cmd+crc
    cmd = cmd+b'\r'
    while len(cmd)<8:
        cmd = cmd+b'\0'
    return cmd

def sendCommand(cmd):
    dev.ctrl_transfer(0x21, 0x9, 0x200, 0, cmd)

def getResult(timeout=100):
    res=""
    i=0
    while '\r' not in res and i<20:
        try:
            res+="".join([chr(i) for i in dev.read(0x81, 8, timeout) if i!=0x00])
        except usb.core.USBError as e:
            if e.errno == 110:
                pass
            else:
                raise
        i+=1
    return res



vendorId = 0x0665
productId = 0x5161
interface = 0
dev = usb.core.find(idVendor=vendorId, idProduct=productId)
if dev.is_kernel_driver_active(interface):
    dev.detach_kernel_driver(interface)
dev.set_interface_altsetting(0,0)

sendCommand(getCommand('QPI'))
res = getResult()
```

After playing a little bit with commands (by changing "QPI" by one of command we can see in trace), I end up with this list of command and corresponding response:

```
In case of invalid command:
(NAKss

QPIRI: Rated Information ?
(230.0 21.7 230.0 50.0 21.7 5000 5000 48.0 48.0 45.5 54.0 54.0 2 30 050 0 2 1 9 20 0 0 51.0 0 1 000Ü

QPIGS: source ?
(226.8 49.9 230.0 49.9 0253 0163 005 393 48.90 000 032 0023 0000 000.0 00.00 00003 00010000 00 00 00000 010

QPGS0: source 0 ?
(1 92931712101861 B 00 229.5 49.98 230.0 49.98 0230 0120 004 48.9 000 032 000.0 000 00230 00120 002 00000010 0 1 050 240 30 00 002Ï

QVFW: Version FirmWare
(VERFW:00076.20

QPIWS
00000000000000000000000000000000000000x

QSID: device ID ?
(1492931712101861005535;´

QBEQI
(0 060 030 050 030 58.40 000 120 0

QMOD:
(BçÉ
```

Response contains 2 crc bytes at the end.

