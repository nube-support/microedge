import pyvisa as visa
import time
import threading, logging, Voltage_Testing
from termcolor import *

# Define the start and end voltage levels
start_voltage = 0  # Starting voltage (in volts)
end_voltage = 3.3    # Ending voltage (in volts)
duration = 10      # Total time to complete the transition (in seconds)
interval = 1       # Time interval for each step (in seconds)
power_supply = None

def turn_on_channels(power_supply):
    # Turn on all channels
    power_supply.write("OUTP CH1, ON")

def turn_off_channels(power_supply):
    # Turn off all channels
    power_supply.write("OUTP CH1, OFF")

def set_voltage(channel, voltage, power_supply):
    command = f"APPL CH{channel},{voltage},{0.1}"
    power_supply.write(command)

def main():
    # Open a connection to the Rigol DP832 power supply
    rm = visa.ResourceManager() 
    usb_resource = "USB0::0x1AB1::0x0E11::DP8C204204520::INSTR"
    power_supply = rm.open_resource(usb_resource)

    turn_on_channels(power_supply)

    # Set the initial voltage for each channel to 0
    power_supply.write("APPL CH1, 0")
    power_supply.write("APPL CH2, 0")

    # Calculate the voltage step size
    voltage_step = 0.5

    # Perform the voltage ramp using threading
    current_voltage = start_voltage

    Voltage_Testing.unlock_micro_edge()

    while current_voltage < end_voltage:
        set_voltage(1, current_voltage,power_supply)

        # Wait for the specified interval
        time.sleep(interval)

        # Measure current and voltage from power supply
        voltage = round(float(power_supply.query(f"MEAS:VOLT? CH1")), 2)
        current = float(power_supply.query(f"MEAS:CURR? CH1"))
        positive_error_margin = round(voltage + voltage * 0.1, 2)
        negative_error_margin = round(voltage - voltage * 0.1, 2)

        micro_edge_voltage_u1 = Voltage_Testing.getVoltage(b'VALUE_UI1_RAW?', 0, 3500)
        micro_edge_voltage_u2 = Voltage_Testing.getVoltage(b'VALUE_UI2_RAW?', 0, 3500)
        micro_edge_voltage_u3 = Voltage_Testing.getVoltage(b'VALUE_UI3_RAW?', 0, 3500)

        if(negative_error_margin <= micro_edge_voltage_u1 <= positive_error_margin):
            logging.info(colored(f"CH 1 -> {voltage} V, {current} A, MicroEdge -> UI1: {micro_edge_voltage_u1} V, UI2: {micro_edge_voltage_u2} V, UI3: {micro_edge_voltage_u3} V", "white", "on_blue"))
        else:
            logging.info(colored(f"CH 1 -> {voltage} V, {current} A, MicroEdge -> UI1: {micro_edge_voltage_u1} V, UI2: {micro_edge_voltage_u2} V, UI3: {micro_edge_voltage_u3} V", "white", "on_red"))

        # Update the current voltage
        current_voltage += voltage_step
    
    turn_off_channels(power_supply)
    time.sleep(2)
    turn_on_channels(power_supply)
    pulse_number = Voltage_Testing.data_pulsesCounter()
    print(pulse_number)
    if(pulse_number == 2):
        logging.info(colored(f"Correct number of pulses received. 2/{pulse_number}", "white", "on_blue"))
    else:
        logging.info(colored(f"Incorrect number of pulses received. Expected 2, got {pulse_number}.", "white", "on_red"))

    # Close the connection to the power supply
    power_supply.close()

if __name__ == '__main__':
    main()