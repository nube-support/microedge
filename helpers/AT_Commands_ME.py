import serial
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-p', metavar='port', type=str,
                    help='Serial port', default='/dev/ME0')
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
parser.add_argument('--no-print', help='Print labels', action='store_true')

args = parser.parse_args()

port = args.p
baud = args.b
timeout = args.t

OK = b'OK'
ERROR = b'ERROR'
UNKNOWN = b'UNKNOWN'

def data_pulsesCounter():
    return checkListNum(b'VALUE_PULSE?', 0, 4294967295)

def getBatteryVoltage():
    return command(b'VALUE_VBAT?', 0, 5.5)

def checkListNum(cmdFull, resp1=0, resp2=1):
    ans = send(cmdFull, OK)
    ans_str = ans.decode('utf-8')
    ans_to_return = float(ans_str)

    return ans_to_return

def unlock_micro_edge():
    string = bytes("LOCK=" + args.w, encoding='utf-8')
    check(string, OK)
    string = bytes("UNLOCK=" + 'N00BIO', encoding='utf-8')
    check(string, OK)   

def command(cmdFull, resp1=0, resp2=1):
    return sendRequest(cmdFull, OK)

def connect_to_me():
    global ser
    port = args.p    
    ser = serial.Serial(port, baud, timeout=timeout)
    print(f"Connected to {port}")
    # If none of the ports worked, raise an exception
    raise Exception("Failed to connect to any available port, ensure correct USB connection.")


def initialize_me():
    time.sleep(0.5)
    command(b'UNLOCK=N00BIO')
    command(b'FACTORYRESET')
    time.sleep(1)
    command(b'UNLOCK=N00BIO')
     
def sendRequest(cmdFull, resp=OK):
    #print(cmdFull)
    retry_count = 0
    while retry_count < 3:
        try:
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

            # Convert the byte string to a string and then to a float
            try:
                value = float(ans.decode('utf-8'))
                #print(f"{cmdFull} {value} {ans.decode('utf-8')}")
                if(cmdFull == b'VALUE_VBAT?'):
                    return value
                if(cmdFull == b'HWVERSION?'):
                    return value
                if(value > 1):
                    value = round((value / 1024) * 3.3, 2)

                    return value

                return value
            except ValueError:
                # Handle the case where conversion to float fails or its a different type like string
                value = ans.decode('utf-8')
        except Exception as e:
            print("Assertion or serial error occurred. Retrying...")
            retry_count += 1
            input('Press reset button on ME and press enter')
            time.sleep(1)  # Add a delay if needed before retrying
        return value

        # # If all retries fail, raise the last encountered exception
        # raise

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
    retry_count = 0
    port = ''
    while retry_count <= 3:
        try:
            port = args.p
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
                #print(line)

            assert(line != b'')

            ans = line[:line.index(b'\n')]
            if resp != UNKNOWN and type == b'?':
                assert(ans.index(b'+') == 0)
                assert(ans.index(b':') == len(cmd) + 1)
                assert(ans[1:ans.index(b':')] == cmd)
                ans = ans[ans.index(b':') + 1:]
            #print('ANS: ', ans)
            return ans
        except  Exception as e:
                print("Serial or assertion error occurred. Retrying...")
                retry_count += 1
                input('Press reset button on ME and press enter')
                time.sleep(1)  # Add a delay if needed before retrying

        # If all retries fail, raise the last encountered exception
        raise