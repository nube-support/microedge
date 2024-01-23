import helpers.AT_Commands_ME as AT_Commands_ME, time
from termcolor import *

def factory_reset():
    AT_Commands_ME.command(b'UNLOCK=N00BIO')
    resp = AT_Commands_ME.command(b'FACTORYRESET')
    pulse_number = int(AT_Commands_ME.data_pulsesCounter())
    print(f"Factory Reset status: {resp} Pulses counter: {pulse_number}")

def check_me_info(seconds):
    print('Real time info from MicroEdge:\n')
    while True:
        micro_edge_voltage_u1 = round(AT_Commands_ME.command(b'VALUE_UI1_RAW?', 0.0, 1.0) * 3.34, 3)    

        time.sleep(0.3)
        micro_edge_voltage_u2 = round(AT_Commands_ME.command(b'VALUE_UI2_RAW?', 0.0, 1.0) * 3.34, 3)
        time.sleep(0.3)
        micro_edge_voltage_u3 = round(AT_Commands_ME.command(b'VALUE_UI3_RAW?', 0.0, 1.0) * 3.34, 3)
        time.sleep(0.3)
        pulse_number = int(AT_Commands_ME.data_pulsesCounter())
        time.sleep(0.3)
        dip_switches = AT_Commands_ME.command(b'VALUE_DIPSWITCHES?')
        
        print(colored(f"MicroEdge -> UI1: {micro_edge_voltage_u1} V, UI2: {micro_edge_voltage_u2} V, UI3: {micro_edge_voltage_u3} V, Pulses: {pulse_number}, Dips: {dip_switches}\n", "white", "on_blue"))
        #input("reset device")
        battery_voltage = AT_Commands_ME.getBatteryVoltage()
        print(colored(f"Battery voltage for ME is: {battery_voltage}V\n", "white", "on_blue"))
        
        time.sleep(seconds)

def main():
    #AT_Commands_ME.connect_to_me()
    #AT_Commands_ME.command(b'UNLOCK=N00BIO')
    #AT_Commands_ME.command(b'UNLOCK=HWVERSION?')

    check_me_info(1)

if __name__ == '__main__':
    main()