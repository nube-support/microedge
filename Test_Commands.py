import serial, logging
import time
import argparse
from serial.serialutil import SerialException


parser = argparse.ArgumentParser()
parser.add_argument('-p', metavar='port', type=str,
                    help='Serial port', default='/dev/ttyACM0')
parser.add_argument('-b', metavar='baud', type=int,
                    help='Serial baudrate', default=115200)
parser.add_argument('-t', metavar='timeout', type=int,
                    help='Serial timeout', default=0.25)
parser.add_argument('-v', metavar='version', type=str,
                    help='Firmware vesion', default='1.0.1-1')
parser.add_argument('-hv', metavar='HW version', type=str,
                    help='Hardware vesion', default='0.1')
parser.add_argument('-w', metavar='password', type=str,
                    help='password', default='N00BIO')
parser.add_argument('-nw', metavar='new password', type=str,
                    help='new password', default='new-N00BIO')
parser.add_argument('-dm', metavar='device make', type=str,
                    help='device make', default='ME')
parser.add_argument('-m', metavar='device model', type=str,
                    help='device model', default='0005')
parser.add_argument('-a', '--all', action='store_true',
                    help='Test all fields', default=False)
parser.add_argument('--prod', action='store_true',
                    help='Speeds up tests for prod builds', default=False)

args = parser.parse_args()

port = args.p
baud = args.b
timeout = args.t

print(port, baud, timeout)
print()

OK = b'OK'
ERROR = b'ERROR'
UNKNOWN = b'UNKNOWN'


def send(cmdFull, resp=OK):
    type = b''
    if b'?' in cmdFull:
        type = b'?'
    elif b'=' in cmdFull:
        type = b'='

    cmd = cmdFull
    if type != b'':
        cmd = cmdFull[:cmdFull.index(type)]
    print('CMD: ', cmdFull)

    while ser.in_waiting:
        ser.readline()
        #  print(ser.readline())

    ser.write(b'AT+')
    ser.write(cmdFull)
    ser.write(b'\n')

    line = None
    while not line or line[0] == b'\0' or line[0] == b'['[0]:
        line = ser.readline()
       # print(line)

    assert(line != b'')

    ans = line[:line.index(b'\n')]
    if resp != UNKNOWN and type == b'?':
        assert(ans.index(b'+') == 0)
        assert(ans.index(b':') == len(cmd) + 1)
        assert(ans[1:ans.index(b':')] == cmd)
        ans = ans[ans.index(b':') + 1:]
    #print('ANS: ', ans)
    return ans


def check(cmdFull, resp=OK):
    ans = send(cmdFull, resp)

    if isinstance(resp, list) and isinstance(resp[0], bytes):
        assert(ans in resp)
    if isinstance(resp, list) and isinstance(resp[0], int):
        assert(len(ans) >= resp[0] and len(ans) <= resp[1])
    elif isinstance(resp, int):
        assert(len(ans) == resp)
    elif isinstance(resp, str):
        assert(ans == bytes(resp, 'utf-8'))
    elif isinstance(resp, bytes):
        assert(ans == resp)

    if args.prod:
        time.sleep(0.02)
    else:
        time.sleep(0.08)

def checkListNum(cmdFull, resp1=0, resp2=1):
    ans = send(cmdFull, OK)

    ans_int = int(ans)
    if ans_int < resp1 or ans_int > resp2:
        assert(ans_int >= resp1 and ans_int <= resp2)

    if args.prod:
        time.sleep(0.02)
    else:
        time.sleep(0.08)
        
def lock():
    check(b'LOCK?', UNKNOWN)
    check(b'LOCK=', ERROR)
    check(b'LOCK=1234', ERROR)
    string = bytes("LOCK=" + args.w, encoding='utf-8')
    check(string, OK)
    if args.prod:
        time.sleep(0.25)
    else:
        time.sleep(0.7)
        
def unlock():
    check(b'UNLOCK?', UNKNOWN)
    check(b'UNLOCK=', ERROR)
    check(b'UNLOCK=1234', ERROR)
    string = bytes("UNLOCK=" + args.w, encoding='utf-8')
    check(string, OK)
    string = bytes("LOCK=" + args.w, encoding='utf-8')
    check(string, OK)
    string = bytes("UNLOCK=" + args.w, encoding='utf-8')
    check(string, OK)

def password():
    check(b'PASSWORD?', UNKNOWN)
    cmd = bytes("PASSWORD=" + args.w + "," + args.nw, encoding='utf-8')
    check(cmd, OK)
    cmd = bytes("PASSWORD=" + args.nw + "," + args.w, encoding='utf-8')
    check(cmd, OK)
    check(b'PASSWORD=', ERROR)
    check(b'PASSWORD=1234', ERROR)
    check(b'PASSWORD', UNKNOWN)


def clearSettStd():
    check(b'CLEARSETTINGSSTD', OK)
    if args.prod:
        time.sleep(0.25)
    else:
        time.sleep(0.7)


def clearSettRbx():
    check(b'CLEARSETTINGSRBX', OK)
    if args.prod:
        time.sleep(0.25)
    else:
        time.sleep(0.7)


def reset():
    check(b'SOFTRESET', OK)
    print('sleeping for 2\n')
    if args.prod:
        time.sleep(1.2)
    else:
        time.sleep(2)
    line = None

    # For USB serial, we need to re-open the serial port after a device reset
    ser.close()
    time.sleep(0.2)
    while True:
        try:
            ser.open()
        except SerialException:
            # try the port number above or below since the reset happens
            #  too fast for PCs to reassign the device to the same port
            serNum = int(ser.port[-1])
            if ser.port == port:
                serNum += 1
            else:
                serNum -= 1
            ser.port = ser.port[:-1]+str(serNum)
            continue
        break
    ser.readline()
    while ser.in_waiting or line != b'':
        line = ser.readline()
        #  print(line)


def uniqueID():
    check(b'UNIQUEID?', 24)
    check(b'UNIQUEID=1', UNKNOWN)
    check(b'UNIQUEID=', UNKNOWN)
    check(b'UNIQUEID', UNKNOWN)

def version():
    check(b'VERSION?', args.v)
    check(b'VERSION=1', UNKNOWN)
    check(b'VERSION=', UNKNOWN)
    check(b'VERSION', UNKNOWN)

def deviceMake():
    check(b'DEVICEMAKE?', args.dm)
    check(b'DEVICEMAKE=1', UNKNOWN)
    check(b'DEVICEMAKE=', UNKNOWN)
    check(b'DEVICEMAKE', UNKNOWN)

def deviceModel():
    check(b'DEVICEMODEL?', args.m)
    check(b'DEVICEMODEL=1', UNKNOWN)
    check(b'DEVICEMODEL=', UNKNOWN)
    check(b'DEVICEMODEL', UNKNOWN)

def deviceVendorID():
    check(b'DEVICEVENDORID?', b'4E55')
    check(b'DEVICEVENDORID=1', UNKNOWN)
    check(b'DEVICEVENDORID=', UNKNOWN)
    check(b'DEVICEVENDORID', UNKNOWN)

def deviceHWVersion():
    check(b'HWVERSION?', args.hv)
    check(b'HWVERSION=1', UNKNOWN)
    check(b'HWVERSION=', UNKNOWN)
    check(b'HWVERSION', UNKNOWN)

def loradetect():
    check(b'LORADETECT?', [b'0', b'1'])
    check(b'LORADETECT=', UNKNOWN)
    check(b'LORADETECT=0', UNKNOWN)
    check(b'LORADETECT', UNKNOWN)

def loramode():
    check(b'LORAMODE?', [b'1', b'2'])
    check(b'LORAMODE=1', OK)
    check(b'LORAMODE?', b'1')
    check(b'LORAMODE=2', OK)
    check(b'LORAMODE?', b'2')
    check(b'LORAMODE=', ERROR)
    check(b'LORAMODE=0', ERROR)
    check(b'LORAMODE=3', ERROR)
    check(b'LORAMODE=12', ERROR)
    check(b'LORAMODE=A', ERROR)

def lrraddr():
    check(b'LRRADDRUNQ?', 8)
    check(b'LRRADDRUNQ=01234567', UNKNOWN)

    check(b'LRRADDRBRD?', 8)
    check(b'LRRADDRBRD=01234567', OK)
    check(b'LRRADDRBRD?', b'01234567')
    check(b'LRRADDRBRD=', ERROR)
    check(b'LRRADDRBRD=012345678', ERROR)
    check(b'LRRADDRBRD=0123456', ERROR)
    check(b'LRRADDRBRD=0123456G', ERROR)

def lrrsub():
    check(b'LRRSUB=1', OK)
    check(b'LRRADDRBRD?', b'FFFFFFAA')
    check(b'LRRSUB=2', OK)
    check(b'LRRADDRBRD?', b'FFFFFFBB')
    check(b'LRRSUB=', ERROR)
    check(b'LRRSUB=0', ERROR)
    check(b'LRRSUB=A', ERROR)
    check(b'LRRSUB=12', ERROR)

def lrrkey():
    check(b'LRRKEY=00112233445566778899AABBCCDDEEFF', OK)
    check(b'LRRKEY=00112233445566778899AABBCCDDEEF', ERROR)
    check(b'LRRKEY=00112233445566778899AABBCCDDEEFFF', ERROR)
    check(b'LRRKEY=', ERROR)
    check(b'LRRKEY?', UNKNOWN)
    pass

def lrwotaa():
    check(b'LRWOTAA?', [b'0', b'1'])
    check(b'LRWOTAA=0', OK)
    check(b'LRWOTAA?', b'0')
    check(b'LRWOTAA=1', OK)
    check(b'LRWOTAA?', b'1')
    check(b'LRWOTAA=', ERROR)
    check(b'LRWOTAA=A', ERROR)
    check(b'LRWOTAA=2', ERROR)
    check(b'LRWOTAA=12', ERROR)


def lrwdeveui():
    check(b'LRWDEVEUI?', 16)
    check(b'LRWDEVEUI=0123456789ABCDEF', OK)
    check(b'LRWDEVEUI?', b'0123456789ABCDEF')
    check(b'LRWDEVEUI=FEDCBA9876543210', OK)
    check(b'LRWDEVEUI?', b'FEDCBA9876543210')
    check(b'LRWDEVEUI=', ERROR)
    check(b'LRWDEVEUI=00000000000000001', ERROR)
    check(b'LRWDEVEUI=000000000000000', ERROR)
    check(b'LRWDEVEUI=000000000000000G', ERROR)


def lrwappeui():
    check(b'LRWAPPEUI?', 16)
    check(b'LRWAPPEUI=0123456789ABCDEF', OK)
    check(b'LRWAPPEUI?', b'0123456789ABCDEF')
    check(b'LRWAPPEUI=FEDCBA9876543210', OK)
    check(b'LRWAPPEUI?', b'FEDCBA9876543210')
    check(b'LRWAPPEUI=', ERROR)
    check(b'LRWAPPEUI=00000000000000001', ERROR)
    check(b'LRWAPPEUI=000000000000000', ERROR)
    check(b'LRWAPPEUI=000000000000000G', ERROR)


def lrwappkey():
    check(b'LRWAPPKEY=00112233445566778899AABBCCDDEEFF', OK)
    check(b'LRWAPPKEY=00112233445566778899AABBCCDDEEF', ERROR)
    check(b'LRWAPPKEY=00112233445566778899AABBCCDDEEFFF', ERROR)
    check(b'LRWAPPKEY=', ERROR)
    check(b'LRWAPPKEY?', UNKNOWN)
    pass


def lrwdevaddr():
    check(b'LRWDEVADDR?', 8)
    check(b'LRWDEVADDR=01234567', OK)
    check(b'LRWDEVADDR?', b'01234567')
    check(b'LRWDEVADDR=FEDCBA98', OK)
    check(b'LRWDEVADDR?', b'FEDCBA98')
    check(b'LRWDEVADDR=', ERROR)
    check(b'LRWDEVADDR=012345678', ERROR)
    check(b'LRWDEVADDR=0123456', ERROR)
    check(b'LRWDEVADDR=0123456G', ERROR)


def lrwnwkskey():
    check(b'LRWNWKSKEY=00112233445566778899AABBCCDDEEFF', OK)
    check(b'LRWNWKSKEY=00112233445566778899AABBCCDDEEF', ERROR)
    check(b'LRWNWKSKEY=00112233445566778899AABBCCDDEEFFF', ERROR)
    check(b'LRWNWKSKEY=', ERROR)
    check(b'LRWNWKSKEY?', UNKNOWN)
    pass


def lrwappskey():
    check(b'LRWAPPSKEY=00112233445566778899AABBCCDDEEFF', OK)
    check(b'LRWAPPSKEY=00112233445566778899AABBCCDDEEF', ERROR)
    check(b'LRWAPPSKEY=00112233445566778899AABBCCDDEEFFF', ERROR)
    check(b'LRWAPPSKEY=', ERROR)
    check(b'LRWAPPSKEY?', UNKNOWN)
    pass


def lorapuben():
    check(b'LORAPUBEN?', [b'0', b'1'])
    check(b'LORAPUBEN=1', OK)
    check(b'LORAPUBEN?', b'1')
    check(b'LORAPUBEN=2', ERROR)
    check(b'LORAPUBEN?', b'1')
    check(b'LORAPUBEN=', ERROR)
    check(b'LORAPUBEN=0', OK)
    check(b'LORAPUBEN?', b'0')
    check(b'LORAPUBEN=2', ERROR)
    check(b'LORAPUBEN=01', ERROR)
    check(b'LORAPUBEN=A', ERROR)


def lorapubsecs():
    checkListNum(b'LORAPUBSECS?', 1, 65535)
    check(b'LORAPUBSECS=10', OK)
    check(b'LORAPUBSECS?', b'10')
    check(b'LORAPUBSECS=60', OK)
    check(b'LORAPUBSECS?', b'60')
    check(b'LORAPUBSECS=', ERROR)
    check(b'LORAPUBSECS=0', ERROR)
    check(b'LORAPUBSECS=2', ERROR)
    check(b'LORAPUBSECS=66000', ERROR)
    check(b'LORAPUBSECS=A', ERROR)

def loraWan_rejoinTime():
    checkListNum(b'LRWREJOINTIME?', 1, 65535)
    check(b'LRWREJOINTIME=240', OK)
    check(b'LRWREJOINTIME?', b'240')
    check(b'LRWREJOINTIME=60', OK)
    check(b'LRWREJOINTIME?', b'60')
    check(b'LRWREJOINTIME=', ERROR)
    check(b'LRWREJOINTIME=0', ERROR)
    check(b'LRWREJOINTIME=2', ERROR)
    check(b'LRWREJOINTIME=66000', ERROR)
    check(b'LRWREJOINTIME=A', ERROR)
    check(b'LRWREJOINTIME', UNKNOWN)


def loraWan_ADR():
    check(b'LRWADR?', [b'0', b'1'])
    check(b'LRWADR=1', OK)
    check(b'LRWADR?', b'1')
    check(b'LRWADR=0', OK)
    check(b'LRWADR?', b'0')
    check(b'LRWADR=', ERROR)
    check(b'LRWADR=2', ERROR)
    check(b'LRWADR=A', ERROR)
    check(b'LRWADR', UNKNOWN)

def loraWan_port():
    checkListNum(b'LRWPORT?', 1, 255)
    check(b'LRWPORT=10', OK)
    check(b'LRWPORT?', b'10')
    check(b'LRWPORT=', ERROR)
    check(b'LRWPORT=-1', ERROR)
    check(b'LRWPORT=256', ERROR)
    check(b'LRWPORT=B', ERROR)
    check(b'LRWPORT', UNKNOWN)

def loraWan_dataRate():
    checkListNum(b'LRWDATARATEDEFAULT?', 0, 15)
    check(b'LRWDATARATEDEFAULT=5', OK)
    check(b'LRWDATARATEDEFAULT?', b'5')
    check(b'LRWDATARATEDEFAULT=', ERROR)
    check(b'LRWDATARATEDEFAULT=-1', ERROR)
    check(b'LRWDATARATEDEFAULT=17', ERROR)
    check(b'LRWDATARATEDEFAULT=B', ERROR)
    check(b'LRWDATARATEDEFAULT', UNKNOWN)

def loraWan_confirmedMSG():
    check(b'LRWCONFIRMEDMSG?', [b'0', b'1'])
    check(b'LRWCONFIRMEDMSG=1', OK)
    check(b'LRWCONFIRMEDMSG?', b'1')
    check(b'LRWCONFIRMEDMSG=0', OK)
    check(b'LRWCONFIRMEDMSG?', b'0')
    check(b'LRWCONFIRMEDMSG=', ERROR)
    check(b'LRWCONFIRMEDMSG=-1', ERROR)
    check(b'LRWCONFIRMEDMSG=17', ERROR)
    check(b'LRWCONFIRMEDMSG=B', ERROR)
    check(b'LRWCONFIRMEDMSG', UNKNOWN)

def loraWan_subBand():
    check(b'DELSUBBAND=1', OK)
    check(b'SUBBAND?', [b'0', b'0,915000000,0'])
    check(b'ADDSUBBAND=0,915000000,0', OK)
    check(b'SUBBAND?', b'0,915000000,0')
    check(b'ADDSUBBAND=1,868000000,1', OK)
    check(b'SUBBAND?', [b'0', b'0,915000000,01,868000000,1'])
    check(b'REVSUBBAND=0', OK)
    check(b'SUBBAND?', b'1,868000000,1')
    check(b'REVSUBBAND=1', OK)
    check(b'SUBBAND?', b'0')
    check(b'DELSUBBAND=2', ERROR)
    check(b'DELSUBBAND', UNKNOWN)
    check(b'SUBBAND', UNKNOWN)
    check(b'ADDSUBBAND', UNKNOWN)
    check(b'ADDSUBBAND=', ERROR)
    check(b'ADDSUBBAND=3', ERROR)
    check(b'ADDSUBBAND=3,33', ERROR)

def loraWan_datarateMin():
    checkListNum(b'LRWDATARATEMIN?', 0, 15)
    check(b'LRWDATARATEMIN=2', OK)
    check(b'LRWDATARATEMIN?', b'2')
    check(b'LRWDATARATEMIN', UNKNOWN)
    check(b'LRWDATARATEMIN=', ERROR)
    check(b'LRWDATARATEMIN=17', ERROR)

def loraWan_datarateMax():
    checkListNum(b'LRWDATARATEMAX?', 0, 15)
    check(b'LRWDATARATEMAX=13', OK)
    check(b'LRWDATARATEMAX?', b'13')
    check(b'LRWDATARATEMAX', UNKNOWN)
    check(b'LRWDATARATEMAX=', ERROR)
    check(b'LRWDATARATEMAX=17', ERROR)


def data_vbat():
    checkListNum(b'VALUE_VBAT?', 0, 5500)
    check(b'VALUE_VBAT=', UNKNOWN)
    check(b'VALUE_VBAT=A', UNKNOWN)
    check(b'VALUE_VBAT', UNKNOWN)


def data_pulsesCounter():
    checkListNum(b'VALUE_PULSE?', 0, 4294967295)
    check(b'VALUE_PULSE=', UNKNOWN)
    check(b'VALUE_PULSE=A', UNKNOWN)
    check(b'VALUE_PULSE', UNKNOWN)

def data_dipswitch():
    ans = send(b'VALUE_DIPSWITCHES?')
    for n in ans:
        if (n ^ 0x30) != 0 and (n ^ 0x30) != 1:
            assert (n == b'0' or n == b'1')
    if args.prod:
        time.sleep(0.02)
    else:
        time.sleep(0.08)
    check(b'VALUE_DIPSWITCHES=', UNKNOWN)
    check(b'VALUE_DIPSWITCHES=A', UNKNOWN)
    check(b'VALUE_DIPSWITCHES', UNKNOWN)

def data_UI1_raw():
    checkListNum(b'VALUE_UI1_RAW?', 0, 3500)
    check(b'VALUE_UI1_RAW=', UNKNOWN)
    check(b'VALUE_UI1_RAW=A', UNKNOWN)
    check(b'VALUE_UI1_RAW', UNKNOWN)

def data_UI2_raw():
    checkListNum(b'VALUE_UI2_RAW?', 0, 3500)
    check(b'VALUE_UI2_RAW=', UNKNOWN)
    check(b'VALUE_UI2_RAW=A', UNKNOWN)
    check(b'VALUE_UI2_RAW', UNKNOWN)

def data_UI3_raw():
    checkListNum(b'VALUE_UI3_RAW?', 0, 3500)
    check(b'VALUE_UI3_RAW=', UNKNOWN)
    check(b'VALUE_UI3_RAW=A', UNKNOWN)
    check(b'VALUE_UI3_RAW', UNKNOWN)

def enterBootloader():
    check(b'ENTERBOOTLOADER?', UNKNOWN)
    check(b'ENTERBOOTLOADER=', UNKNOWN)
    check(b'ENTERBOOTLOADER=A', UNKNOWN)
    check(b'ENTERBOOTLOADER', OK)    


def appSettingsTest():
    # clear rbx
    clearSettRbx()
    reset()

    def_mode = send(b'LORAMODE?')
    def_addr_brd = send(b'LRRADDRBRD?')
    def_otaa = send(b'LRWOTAA?')
    def_eui = send(b'LRWDEVEUI?')
    def_pub_en = send(b'LORAPUBEN?')
    def_pub_sec = send(b'LORAPUBSECS?')

    # set
    check(b'LORAMODE=1', OK)
    check(b'LRRADDRBRD=01234567', OK)
    check(b'LRWOTAA=0', OK)
    check(b'LRWDEVEUI=0123456789ABCDEF', OK)
    check(b'LORAPUBEN=1', OK)
    check(b'LORAPUBSECS=10', OK)

    # clear
    clearSettStd()
    reset()

    # test
    check(b'LORAMODE?', b'1')
    check(b'LRRADDRBRD?', b'01234567')
    check(b'LRWOTAA?', b'0')
    check(b'LRWDEVEUI?', b'0123456789ABCDEF')
    check(b'LORAPUBEN?', b'1')
    check(b'LORAPUBSECS?', b'10')

    # clear
    clearSettStd()
    reset()

    # set
    check(b'LORAMODE=2', OK)
    check(b'LRRADDRBRD=ABCDEF01', OK)
    check(b'LRWOTAA=1', OK)
    check(b'LRWDEVEUI=FEDCBA9876543210', OK)
    check(b'LORAPUBEN=0', OK)
    check(b'LORAPUBSECS=60', OK)

    # clear
    clearSettStd()
    reset()

    # test
    check(b'LORAMODE?', b'2')
    check(b'LRRADDRBRD?', b'ABCDEF01')
    check(b'LRWOTAA?', b'1')
    check(b'LRWDEVEUI?', b'FEDCBA9876543210')
    check(b'LORAPUBEN?', b'0')
    check(b'LORAPUBSECS?', b'60')

    # clear
    clearSettRbx()
    reset()

    # test defaults
    check(b'LORAMODE?', def_mode)
    check(b'LRRADDRBRD?', def_addr_brd)
    check(b'LRWOTAA?', def_otaa)
    check(b'LRWDEVEUI?', def_eui)
    check(b'LORAPUBEN?', def_pub_en)
    check(b'LORAPUBSECS?', def_pub_sec)


class bcolors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def test(func):
    print(f'->{bcolors.BOLD} {func.__name__}{bcolors.ENDC}')
    func()
    print(f'{bcolors.GREEN}  PASSED{bcolors.ENDC}')
    with open("output.txt", "a") as output_file:
        output_file.write(f"{func.__name__} -> PASSED\n")
with serial.Serial(port, baud, timeout=timeout) as ser:
    ser.readline()
    while ser.in_waiting:
        ser.readline()

    start_time = time.time()

    test(lock)
    test(unlock)
    test(password)
    test(uniqueID)
    test(version)
    test(deviceMake)
    test(deviceModel)
    test(deviceVendorID)
    test(deviceHWVersion)

    test(loramode)
    test(loradetect)
    test(loradetect)
    test(lrraddr)
    test(lrrsub)
    test(lrrkey)
    test(lrwotaa)
    test(lrwdeveui)
    test(lrwappeui)
    test(lrwappkey)
    test(lrwdevaddr)
    test(lrwnwkskey)
    test(lrwappskey)
    test(lorapuben)
    test(lorapubsecs)
    test(loraWan_rejoinTime)
    test(loraWan_ADR)
    test(loraWan_port)
    test(loraWan_dataRate)
    test(loraWan_confirmedMSG)
    test(loraWan_subBand)
    test(loraWan_datarateMin)
    test(loraWan_datarateMax)

    test(data_vbat)
    test(data_pulsesCounter)
    test(data_dipswitch)
    test(data_UI1_raw)
    test(data_UI2_raw)
    test(data_UI3_raw)

    if args.all:
        test(appSettingsTest)

    test(enterBootloader)

print(f'{bcolors.BOLD}{bcolors.GREEN}PASSED{bcolors.ENDC}')
print(f'Tests completed in: {round(time.time()-start_time, 2)}s')