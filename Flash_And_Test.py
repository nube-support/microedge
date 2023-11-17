import subprocess
import Custom_Logger, logging, Manufacturing_Info, Rigol_Power_Supply, Generate_MicroEdge_Labels
import sys, shutil, time
from termcolor import *

local_test_path = f"/home/testbench/product_database/"

# Check if argument not to print has been passed in the terminal
print_flag = ''
if len(sys.argv) > 1 and print_flag == '':
    if sys.argv[1] == '--no-print':
        print_flag = sys.argv[1]

technician, hardware_version, batch_id, manufacturing_order = None, None, None, None
Custom_Logger.create_logger('output.txt')  # Set up the custom logging configuration

def run_subprocess(command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            # Log the subprocess output
            logging.info(line.strip())

        # Wait for the process to finish
        process.wait()

        # Log the process return code
        logging.info(f"Subprocess finished with return code: {process.returncode}")

    except Exception as e:
        logging.error(f"Error running subprocess: {e}")

while True:
    #make sure the test output file is clean for each device
    with open('output.txt', "w") as file:
        file.truncate(0)

    # Check if technician and info is still the same
    if None not in (technician, hardware_version, batch_id, manufacturing_order):
        input(colored('Press the reboot button to ensure the next device is ready to be tested.\n', 'white', 'on_blue'))
        technician, hardware_version, batch_id, manufacturing_order = Manufacturing_Info.current_technician_and_info(technician, hardware_version, batch_id, manufacturing_order)
    else:
        # First execution of script, get technician and info
        technician, hardware_version, batch_id, manufacturing_order = Manufacturing_Info.current_technician_and_info()
        input(colored('Put device into boot mode and Press ENTER to execute the script to flash and test the device.\n', 'white', 'on_blue'))
    # Delete all data on the Pi to make sure it is ready to be flashed
    subprocess.run(["sudo", "/home/testbench/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI", "-c", "port=usb1", "-e", "all"])
    
    logging.info("Pi succesfully prepared for flashing.\n")

    # Flash
    subprocess.run(["sudo", "/home/testbench/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI", "-c", "port=usb1", "-d", "/home/testbench/MicroEdge/rubix-micro-edge_v1.0.1-1_DEBUG.bin", "0x08000000"])
    logging.info(f"Pi succesfully flashed.\n")

    # Reboot
    subprocess.run(["sudo", "/home/testbench/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI", "-c", "port=usb1", "-g"])

    #subprocess.run(["sudo", "/home/testbench/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI", "-c", "port=usb1", "-log", "trace.log"])
    input("Remove and re-insert the USB C cable from the PCB and press Enter to test device")
    

    logging.info("Started tests.\n")

    # Test commands on Micro Edge
    subprocess.run(["sudo", "python3", "Test_Commands.py"])

    # Test Voltage and Current 
    #Rigol_Power_Supply.main()

    # Dummy barcode and software version
    barcode = "ME-04-XXXXXXXX"
    software_version = "1.0.1"

    # Copy the contents of the old file to the new file, TODO get the correct info to generate the barcode, LoraID from ME, some sort of ssh or info via usb
    shutil.copyfile('output.txt', f"{local_test_path}{barcode}.txt")

    Generate_MicroEdge_Labels.main(barcode, hardware_version, software_version)

    # Run pyserial-miniterm, probably where we get the LoraID
    input(colored('Press the reset button on the device once the Miniterm text comes up, press ENTER to continue.\n', 'white', 'on_blue'))

    run_subprocess(["pyserial-miniterm", "/dev/ttyUSB1", "38400"])


    # try:
    #     command = "sudo pyserial-miniterm /dev/ttyUSB1 38400"

    #     # Set a timeout (e.g., 2 seconds)
    #     timeout = 2

    #     with open('output.txt', 'a') as output_file:
    #         result = subprocess.run(
    #             command, shell=True, stdout=output_file, stderr=subprocess.PIPE, text=True, timeout=timeout
    #         )
    #         logging.info(result)

    #     if result.returncode == 0:
    #         # Command succeeded
    #         print("Command succeeded.")
    #     else:
    #         # Command failed
    #         print("Command failed. Error:")
    #         print(result.stderr)

    # except subprocess.TimeoutExpired:
    #     # Handle a timeout here
    #     print("Succesfully retrieved test information")




