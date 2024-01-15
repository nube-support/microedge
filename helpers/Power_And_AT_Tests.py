import pyvisa as visa
import time
import subprocess, logging, helpers.AT_Commands_ME as AT_Commands_ME
from termcolor import *

# Define the start and end voltage levels
start_voltage = 0  # Starting voltage (in volts)
end_voltage = 3.3    # Ending voltage (in volts)
duration = 10      # Total time to complete the transition (in seconds)
interval = 1    # Time interval for each step (in seconds)
power_supply = None

def turn_on_channels(power_supply, channels):
    # Turn on all channels
    for channel in channels:
        power_supply.write(f"OUTP {channel}, ON")

def turn_off_channels(power_supply, channels):
    # Turn off all channels
    for channel in channels:
        power_supply.write(f"OUTP {channel}, OFF")

def set_voltage(channel, voltage, power_supply):
    command = f"APPL CH{channel},{voltage},{0.5}"
    power_supply.write(command)

def main(power_supply, make, model, variant):
    comments = ''

    # Calculate the voltage step size
    voltage_step = 0.5

    # Perform the voltage ramp using threading
    current_voltage = start_voltage

    AT_Commands_ME.command(b'UNLOCK=N00BIO')     
    AT_Commands_ME.command(b'FACTORYRESET')
    time.sleep(1)

    AT_Commands_ME.command(b'UNLOCK=N00BIO')     

    pulse_number = int(AT_Commands_ME.data_pulsesCounter())

    if(pulse_number == 0):
        logging.info(colored(f"Working - Initial pulse numbers at {pulse_number}, correct.", "white", "on_green"))
    else:
        logging.info(colored(f"Failed - Initial pulse numbers at {pulse_number}, wrong.", "white", "on_red"))

    unique_id = AT_Commands_ME.command(b'UNIQUEID?')
    logging.info(colored(f"Unique ID: {unique_id}", "white", "on_blue"))
    AT_Commands_ME.command(b'HWVERSION=1.2')
    
    fw_version = AT_Commands_ME.command(b'FWVERSION?')
    logging.info(colored(f"Firmware Version: {fw_version}", "white", "on_blue"))
    
    hw_version = AT_Commands_ME.command(b'HWVERSION?')
    logging.info(colored(f"Hardware Version: {hw_version}", "white", "on_blue"))

    make = AT_Commands_ME.command(b'DEVICEMAKE?')
    logging.info(colored(f"Make: {make}", "white", "on_blue"))

    #model = AT_Commands_ME.command(b'DEVICEMODEL?')
    logging.info(colored(f"Model: {model}", "white", "on_blue"))

    logging.info(colored(f"Variant: {variant}", "white", "on_blue"))

    loraID = AT_Commands_ME.command(b'LRRADDRUNQ?')
    logging.info(colored(f"loRaID: {loraID}", "white", "on_blue"))

    push = AT_Commands_ME.command(b'LORARAWPUSH')
    if(push == 'OK'):
        logging.info(colored(f"Push: {push}", "white", "on_blue"))
        comments += 'LoraPush,'
    else:
        logging.info(colored(f"Failed to push LoRa package.", "white", "on_red"))
    time.sleep(0.5)

    lora_detect = AT_Commands_ME.command(b'LORADETECT?')
    logging.info(colored(f"Lora Detected: {lora_detect}", "white", "on_blue"))

    dip_switches = AT_Commands_ME.command(b'VALUE_DIPSWITCHES?')

    if(dip_switches == '[0,0,0,0,0,0,0,0]'):
        logging.info(colored(f"Dip Switches: {dip_switches}", "white", "on_blue"))
        comments += 'DipSwitches,'
    else:
        logging.info(colored(f"Failed - Dip Switches, Incorrect", "white", "on_red"))


    #turn_on_channels(power_supply, ['CH1', 'CH2'])
    voltage_test_success = True
    battery_voltage_test_success = True
    battery_voltage_test_value = 3.8
    while (battery_voltage_test_value >= 3.0):
        if(battery_voltage_test_value > 3.0):
            set_voltage(2, battery_voltage_test_value, power_supply)
            turn_off_channels(power_supply, ['CH1','CH2'])
            time.sleep(1.5)
            print("turned off channels")
            turn_on_channels(power_supply, ['CH1','CH2'])
            time.sleep(1.5)
            print("turned on channels")

            time.sleep(0.5)

        #get actual voltage reading from ch2 to be as close as possible
        voltage_ch2 = round(float(power_supply.query(f"MEAS:VOLT? CH2")), 2)
        time.sleep(1)

        #input(colored("Press rest button, wait red light blinking and press enter:"))
        #battery_voltage = AT_Commands_ME.getBatteryVoltage()
        #time.sleep(0.5)
        battery_voltage = AT_Commands_ME.getBatteryVoltage()

        #logging.info(colored(f"Battery voltage for ME is: {battery_voltage}V", "white", "on_blue"))
        positive_battery_error_margin = round(voltage_ch2 + voltage_ch2 * 0.02, 2)
        negative_battery_error_margin = round(voltage_ch2 - voltage_ch2 * 0.02, 2)

        print(positive_battery_error_margin)
        print(negative_battery_error_margin)
        if(negative_battery_error_margin <= battery_voltage <= positive_battery_error_margin):
            logging.info(colored(f"Battery reading for ME is: {battery_voltage}, test value is: {voltage_ch2}", "white", "on_blue"))
        else:
            logging.info(colored(f"Battery reading for ME is: {battery_voltage}, test value is: {voltage_ch2}", "white", "on_red"))
            battery_voltage_test_success = False

        battery_voltage_test_value -= 0.2

    set_voltage(2, 3.8, power_supply)
    while current_voltage < end_voltage:
        set_voltage(1, current_voltage,power_supply)
        # Wait for the specified interval
        time.sleep(interval)
    
        # Measure current and voltage from power supply
        voltage = round(float(power_supply.query(f"MEAS:VOLT? CH1")), 2)
        current = float(power_supply.query(f"MEAS:CURR? CH1"))
        positive_error_margin = round(voltage + voltage * 0.1, 2)
        negative_error_margin = round(voltage - voltage * 0.1, 2)
        micro_edge_voltage_u1 = 0.0
        micro_edge_voltage_u2 = 0.0
        micro_edge_voltage_u3 = 0.0
        turn_off_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_on_channels(power_supply, ['CH1'])
        #input("reset")
        micro_edge_voltage_u1 = round(AT_Commands_ME.command(b'VALUE_UI1_RAW?', 0.0, 1.0) * 3.34, 3)
        time.sleep(0.3)
        micro_edge_voltage_u2 = round(AT_Commands_ME.command(b'VALUE_UI2_RAW?', 0.0, 1.0) * 3.34, 3)
        time.sleep(0.3)

        micro_edge_voltage_u3 = round(AT_Commands_ME.command(b'VALUE_UI3_RAW?', 0.0, 1.0) * 3.34, 3)

        if(current_voltage > 0):
            while(micro_edge_voltage_u1 == 0.0 or micro_edge_voltage_u2 == 0.0 or micro_edge_voltage_u3 == 0.0):
                micro_edge_voltage_u1 = round(AT_Commands_ME.command(b'VALUE_UI1_RAW?', 0.0, 1.0) * 3.34, 3)
                micro_edge_voltage_u2 = round(AT_Commands_ME.command(b'VALUE_UI2_RAW?', 0.0, 1.0) * 3.34, 3)
                micro_edge_voltage_u3 = round(AT_Commands_ME.command(b'VALUE_UI3_RAW?', 0.0, 1.0) * 3.34, 3)

        voltages = [micro_edge_voltage_u1, micro_edge_voltage_u2, micro_edge_voltage_u3]

        if all(negative_error_margin <= voltage <= positive_error_margin for voltage in voltages):
            logging.info(colored(f"OUTPUT -> {voltage} V, {current} A, MicroEdge -> UI1: {voltages[0]} V, UI2: {voltages[1]} V, UI3: {voltages[2]} V", "white", "on_blue"))
        else:
            logging.info(colored(f"OUTPUT -> {voltage} V, {current} A, MicroEdge -> UI1: {voltages[0]} V, UI2: {voltages[1]} V, UI3: {voltages[2]} V", "white", "on_red"))
            voltage_test_success = False

        # Update the current voltage
        current_voltage += voltage_step

    if(battery_voltage_test_success):
        comments += 'Battery,'
    if(voltage_test_success):
        comments += 'Voltage,'
    
    logging.info('')
    turn_off_channels(power_supply, ['CH1'])
    time.sleep(0.5)
    turn_on_channels(power_supply, ['CH1'])
    time.sleep(0.5)
    turn_off_channels(power_supply, ['CH1'])
    time.sleep(0.5)
    turn_on_channels(power_supply, ['CH1'])

    pulse_number = AT_Commands_ME.data_pulsesCounter()

    if(pulse_number == 2):
        logging.info(colored(f"Correct number of pulses received. 2/{int(pulse_number)}\n", "white", "on_green"))
        comments += 'Pulses,'
    else:
        logging.info(colored(f"Incorrect number of pulses received. Expected 2, got {int(pulse_number)}.\n", "white", "on_red"))

    #turn_off_channels(power_supply)

    # Close the connection to the power supply
    #power_supply.close()

    return loraID, fw_version, hw_version, unique_id, comments
if __name__ == '__main__':
    main()
