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

OK = b'OK'
ERROR = b'ERROR'
UNKNOWN = b'UNKNOWN'

def data_pulsesCounter():
    return checkListNum(b'VALUE_PULSE?', 0, 4294967295)

def checkListNum(cmdFull, resp1=0, resp2=1):
    ans = send(cmdFull, OK)
    ans_int = int(ans)
    return ans_int

def unlock_micro_edge():
    string = bytes("LOCK=" + args.w, encoding='utf-8')
    check(string, OK)
    string = bytes("UNLOCK=" + 'N00BIO', encoding='utf-8')
    check(string, OK)   

def getVoltage(cmdFull, resp1=0, resp2=1):
    return sendRequest(cmdFull, OK)

def sendRequest(cmdFull, resp=OK):
    ser = serial.Serial(port, baud, timeout=timeout)
    type = b''
    if b'?' in cmdFull:
        type = b'?'
    elif b'=' in cmdFull:
        type = b'='

    cmd = cmdFull
    if type != b'':
        cmd = cmdFull[:cmdFull.index(type)]

    while ser.in_waiting:
        ser.readline()
        #print(ser.readline())

    ser.write(b'AT+')
    ser.write(cmdFull)
    ser.write(b'\n')

    line = None
    while not line or line[0] == b'\0' or line[0] == b'['[0]:
        line = ser.readline()
        #print(line)
    #print('yay')
    #print(line)
    assert(line != b'')

    ans = line[:line.index(b'\n')]

    if resp != UNKNOWN and type == b'?':
        assert(ans.index(b'+') == 0)
        assert(ans.index(b':') == len(cmd) + 1)
        assert(ans[1:ans.index(b':')] == cmd)
        ans = ans[ans.index(b':') + 1:]
    #print('ANS: ', ans)
    # Convert the byte string to a string and then to a float
    value = float(ans.decode('utf-8'))

    converted_value = round((value / 1024) * 3.3, 2)
    #print(converted_value)
    return converted_value


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

def send(cmdFull, resp=OK):
    ser = serial.Serial(port, baud, timeout=timeout)

    type = b''
    if b'?' in cmdFull:
        type = b'?'
    elif b'=' in cmdFull:
        type = b'='

    cmd = cmdFull
    if type != b'':
        cmd = cmdFull[:cmdFull.index(type)]

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