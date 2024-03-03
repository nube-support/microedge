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


def measure_voltage(power_supply):
    return round(float(power_supply.query("MEAS:VOLT? CH1")), 2)

def measure_current(power_supply):
    return float(power_supply.query("MEAS:CURR? CH1"))

def measure_micro_edge_voltage(command):
    raw_value = AT_Commands_ME.command(command, 0.0, 1.0)
    return round(raw_value * 3.34, 3)

def check_retry_conditions(voltage_measurements, target_voltage, error_margin):
    return any(abs(voltage - target_voltage) > error_margin for voltage in voltage_measurements) or any(voltage == 0.033 for voltage in voltage_measurements)


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

    # AT_Commands_ME.command(b'UNLOCK=N00BIO')     
    # AT_Commands_ME.command(b'FACTORYRESET')
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
    time.sleep(0.4)
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
            time.sleep(1)
            turn_on_channels(power_supply, ['CH1','CH2'])
            time.sleep(1)

        #get actual voltage reading from ch2 to be as close as possible
        voltage_ch2 = round(float(power_supply.query(f"MEAS:VOLT? CH2")), 2)

        #incorrect reading from power supply safe guard
        if(voltage_ch2 < 3):
            continue

        time.sleep(1)
        
        #input(colored("Press rest button, wait red light blinking and press enter:"))
        #battery_voltage = AT_Commands_ME.getBatteryVoltage()
        #time.sleep(0.5)
        battery_voltage = AT_Commands_ME.getBatteryVoltage()

        #logging.info(colored(f"Battery voltage for ME is: {battery_voltage}V", "white", "on_blue"))
        positive_battery_error_margin = round(voltage_ch2 + voltage_ch2 * 0.02, 2)
        negative_battery_error_margin = round(voltage_ch2 - voltage_ch2 * 0.02, 2)

        if(negative_battery_error_margin <= battery_voltage <= positive_battery_error_margin):
            logging.info(colored(f"Battery reading for ME is: {battery_voltage}, test value is: {voltage_ch2}", "white", "on_blue"))
        else:
            logging.info(colored(f"Battery reading for ME is: {battery_voltage}, test value is: {voltage_ch2}", "white", "on_red"))
            battery_voltage_test_success = False

        battery_voltage_test_value -= 0.2

    set_voltage(2, 3.8, power_supply)
    current_voltage = start_voltage
    while current_voltage < end_voltage:
        set_voltage(1, current_voltage, power_supply)
        time.sleep(interval)

        raw_voltage = measure_voltage(power_supply)
        voltage = round(raw_voltage, 2)

        current = measure_current(power_supply)
        positive_error_margin = round(voltage + voltage * 0.1, 2)
        negative_error_margin = round(voltage - voltage * 0.1, 2)

        micro_edge_voltages = [
            measure_micro_edge_voltage(b'VALUE_UI1_RAW?'),
            measure_micro_edge_voltage(b'VALUE_UI2_RAW?'),
            measure_micro_edge_voltage(b'VALUE_UI3_RAW?')
        ]

        turn_off_channels(power_supply, ['CH1'])
        time.sleep(1)
        turn_on_channels(power_supply, ['CH1'])

        retry = False
        retry_iteration = 0
        for i in range(3):
            if abs(micro_edge_voltages[i] - voltage) > 0.2 or micro_edge_voltages[i] == 0.033:
                retry = True
                retry_iteration += 1

        if current_voltage > 0:
            while any(voltage == 0.0 or retry for voltage in micro_edge_voltages):
                retry = False
                micro_edge_voltages = [
                    measure_micro_edge_voltage(b'VALUE_UI1_RAW?'),
                    measure_micro_edge_voltage(b'VALUE_UI2_RAW?'),
                    measure_micro_edge_voltage(b'VALUE_UI3_RAW?')
                ]

                if check_retry_conditions(micro_edge_voltages, voltage, positive_error_margin):
                    retry = True
                    retry_iteration += 1

        # Retry until the conditions are met
        while retry:
            micro_edge_voltages = [
                measure_micro_edge_voltage(b'VALUE_UI1_RAW?'),
                measure_micro_edge_voltage(b'VALUE_UI2_RAW?'),
                measure_micro_edge_voltage(b'VALUE_UI3_RAW?')
            ]
            retry_iteration += 1
            if not check_retry_conditions(micro_edge_voltages, voltage, positive_error_margin):
                retry = False

        if all(negative_error_margin <= voltage <= positive_error_margin for voltage in micro_edge_voltages) and not retry:
            log_color = "white", "on_blue"
        elif all(voltage == 0.0 for voltage in micro_edge_voltages):
            log_color = "white", "on_blue"
        else:
            log_color = "white", "on_red"
            voltage_test_success = False
        log_message = f"OUTPUT -> {voltage} V, {current} A, MicroEdge -> UI1: {micro_edge_voltages[0]} V, UI2: {micro_edge_voltages[1]} V, UI3: {micro_edge_voltages[2]} V"
        logging.info(colored(log_message, *log_color))

        current_voltage += voltage_step

    logging.info(colored(f"\nNumber of retries for voltage counting was: {retry_iteration}", "white", "on_blue"))
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
    time.sleep(1)
    pulse_number = AT_Commands_ME.data_pulsesCounter()

    if(pulse_number == 6):
        logging.info(colored(f"Correct number of pulses received. 6/{int(pulse_number)}\n", "white", "on_green"))
        comments += 'Pulses,'
    elif(pulse_number == 5):

        factory_reset = AT_Commands_ME.command(b'FACTORYRESET')
        while (factory_reset == 'ERROR'):
            AT_Commands_ME.command(b'UNLOCK=N00BIO')
            time.sleep(1)
            print(f"Reset for correct pulse counting: {factory_reset}")
            factory_reset = AT_Commands_ME.command(b'FACTORYRESET')

        time.sleep(0.5)
        turn_off_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_on_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_off_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_on_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_off_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_on_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_off_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_on_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_off_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_on_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_off_channels(power_supply, ['CH1'])
        time.sleep(0.5)
        turn_on_channels(power_supply, ['CH1'])
        time.sleep(1)
        pulse_number = AT_Commands_ME.data_pulsesCounter()
        print(pulse_number)
        if(pulse_number == 6):
            logging.info(colored(f"Correct number of pulses received. 6/{int(pulse_number)}\n", "white", "on_green"))
            comments += 'Pulses,'
    else:
        logging.info(colored(f"Incorrect number of pulses received. Expected 6, got {int(pulse_number)}.\n", "white", "on_red"))

    #turn_off_channels(power_supply)

    # Close the connection to the power supply
    #power_supply.close()

    return loraID, fw_version, hw_version, unique_id, comments
if __name__ == '__main__':
    main()
