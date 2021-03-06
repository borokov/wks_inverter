import usb.core, usb.util, usb.control
import crc16
import datetime
import time
from influxdb import InfluxDBClient
import json
import traceback


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

def get_frame(timeout=500):
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
                    if e.errno == 110: # timeout. This happen quite often
                        pass
                    else:
                        print(traceback.format_exc())
                        raise
                i+=1

            if len(res) < 3:
                error = True
                break;

            crc = res[len(res)-3:-1]
            values = res[:-3]

            frame_crc_int = int.from_bytes([ord(crc[0]), ord(crc[1])], 'big')
            computed_crc_int = crc16.crc16xmodem(values.encode('utf-8'))

            if frame_crc_int != computed_crc_int:
                error = True

            if len(values) < 2:
                error = True

            if not error:
                #print("ok")
                ok = True

        except Exception as e:
            error = True
            raise
        

    return values

class QPGS0(object):
    def __init__(self, frame):
        # ensure first '(' is removed
        if frame[0] == '(':
            frame = frame[1:]

        value_array = frame.split(' ')

        self.a = int(value_array[0]) # 1
        self.b = value_array[1] # 92931712101861 
        self.c = value_array[2] # L
        self.d = float(value_array[3]) # 0
        self.e_voltage_1 = float(value_array[4]) # ~g: Tension de sortie onduleur non stabilisé (EDF ?) [V]
        self.f = float(value_array[5]) # =h: Tension batterie ? Frequence sortie ?
        self.g_voltage_2 = float(value_array[6]) # ~e: Tension de sortie onduleur stabilisé [V]
        self.h_voltage_3 = float(value_array[7]) # =f: Frequence sortie ? [HZ]
        self.i = int(value_array[8]) # =q power [VA] en sortie
        self.j = int(value_array[9]) # =r power [W] en sortie
        self.k = float(value_array[10]) # charge en %
        self.l = float(value_array[11]) # Frequence sortie ? (~50)
        self.m = int(value_array[12]) # =p Puissance solaire [A?] Qui passe a 0 quand on est pas en bypass ?
        self.n = int(value_array[13]) #
        self.o = float(value_array[14]) # tension solaire ? [V]
        self.p = int(value_array[15]) # =o Puissance solaire [A?] Qui passe a 0 quand on est pas en bypass ?
        self.q = int(value_array[16]) # =i: power [VA] en sortie
        self.r = int(value_array[17]) # =j: power [W] en sortie
        self.s = int(value_array[18]) # =k charge en %
        self.t = value_array[19] # 10100010 : bypass - ? - in solar - ? - ? - batterie - ?
        # bitfield
        self.t_0 = int(value_array[19][0]) # pas bypass ?
        self.t_1 = int(value_array[19][1])
        self.t_2 = int(value_array[19][2]) # in solar ?
        self.t_3 = int(value_array[19][3])
        self.t_4 = int(value_array[19][4])
        self.t_5 = int(value_array[19][5]) # Passage en full solaire ?
        self.t_6 = int(value_array[19][6]) # batterie en charge ?
        self.t_7 = int(value_array[19][7])

        self.u = int(value_array[20]) # 0
        self.v = int(value_array[21]) # 1
        self.w = int(value_array[22]) # 50
        self.x = int(value_array[23]) # 240
        self.y = int(value_array[24]) # 30
        self.z = int(value_array[25]) # puissance solaire [A?]
        self.z1 = int(value_array[26]) # 0

    def __str__(self):
        str = ""
        for member in sorted(self.__dict__):
            str += ("{}: {}\n".format(member, self.__dict__[member]))
        return str

    def to_json(self):
        return json.dumps(self.__dict__)

    def send(self):
        pointValues = {
            "measurement": "solar.QPSG0",
            "fields": self.__dict__,
        }
        #print(pointValues)

        client.write_points([pointValues])

class QPIGS(object):
    def __init__(self, frame):
        # ensure first '(' is removed
        if frame[0] == '(':
            frame = frame[1:]

        value_array = frame.split(' ')

        self.a = float(value_array[0]) #
        self.b = float(value_array[1]) #
        self.c = float(value_array[2]) #
        self.d = float(value_array[3]) #
        self.e = int(value_array[4]) #
        self.f = int(value_array[5]) #
        self.g = int(value_array[6]) #
        self.h = int(value_array[7]) #
        self.i = float(value_array[8]) #
        self.j = int(value_array[9]) #
        self.k = int(value_array[10]) #
        self.l = int(value_array[11]) #
        self.m = int(value_array[12]) #
        self.n = float(value_array[13]) #
        self.o = float(value_array[14]) #
        self.p = int(value_array[15]) #
        self.q = int(value_array[16]) #
        self.r = int(value_array[17]) #
        self.s = int(value_array[18]) #
        self.t = value_array[19] #
        self.u = value_array[20] #

    def __str__(self):
        str = ""
        for member in sorted(self.__dict__):
            str += ("{}: {}\n".format(member, self.__dict__[member]))
        return str

    def to_json(self):
        return json.dumps(self.__dict__)

    def send(self):
        pointValues = {
            "measurement": "solar.QPIGS",
            "fields": self.__dict__,
        }
        # print(pointValues)

        client.write_points([pointValues])


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
    try:
        sendCommand('QPGS0')
        res = get_frame()

        client = InfluxDBClient("plusdepanda.no-ip.org", 8086, "root", "root", "EDF")

        qpgs0 = QPGS0(res)
        qpgs0.send()

        sendCommand('QPIGS')
        res = get_frame()
        qpigs = QPIGS(res)
        qpigs.send()

        client.close()

        time.sleep(10)
    except ValueError:
        client.close()
        pass
    except IndexError:
        client.close()
        pass
    except usb.core.USBError:
        print(traceback.format_exc())
        client.close()
        pass
    except Exception:
        print(traceback.format_exc())
        client.close()
        raise
