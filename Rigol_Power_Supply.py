import pyvisa as visa
import time
import threading, logging
from termcolor import *

# Define the start and end voltage levels
start_voltage = 0  # Starting voltage (in volts)
end_voltage = 3    # Ending voltage (in volts)
duration = 10      # Total time to complete the transition (in seconds)
interval = 1       # Time interval for each step (in seconds)
power_supply = None

def turn_on_channels(power_supply):
    # Turn on all channels
    power_supply.write("OUTP CH1, ON")
    power_supply.write("OUTP CH2, ON")
    # Uncomment the line below if there is a third channel
    # power_supply.write("OUTP CH3, ON")

def turn_off_channels(power_supply):
    # Turn off all channels
    power_supply.write("OUTP CH1, OFF")
    power_supply.write("OUTP CH2, OFF")
    # Uncomment the line below if there is a third channel
    # power_supply.write("OUTP CH3, OFF")

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
    power_supply.write("APPL CH1, 0, 0.1")
    power_supply.write("APPL CH2, 0, 0.1")

    # Calculate the voltage step size
    voltage_step = (end_voltage - start_voltage) / (duration / interval)

    # Perform the voltage ramp using threading
    current_voltage = start_voltage

    while current_voltage < end_voltage:
        # Create threads for setting voltage on both channels
        thread1 = threading.Thread(target=set_voltage, args=(1, current_voltage,power_supply))
        thread2 = threading.Thread(target=set_voltage, args=(2, current_voltage, power_supply))

        # Start the threads
        thread1.start()
        thread2.start()

        # Wait for both threads to finish
        thread1.join()
        thread2.join()

        # Wait for the specified interval
        time.sleep(interval)
        
        # Measure current and voltage from power supply
        voltage = float(power_supply.query(f"MEAS:VOLT? CH1"))
        current = float(power_supply.query(f"MEAS:CURR? CH1"))
        
        # TODO GET INFO FROM THE MICROEDGE TO COMPARE
        logging.info(colored(f"Channel 1 - Voltage: {voltage} V, Current: {current} A, MicroEdge - Voltage: XX V, Current: XX A", "white", "on_blue"))
        # Update the current voltage
        current_voltage += voltage_step


    # Ensure that the final voltage is exactly the desired end voltage
    power_supply.write(f"APPL CH1,{end_voltage},{0.1}")
    power_supply.write(f"APPL CH2,{end_voltage},{0.1}")

    # Close the connection to the power supply
    power_supply.close()
