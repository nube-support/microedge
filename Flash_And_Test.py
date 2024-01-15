import subprocess,json
import helpers.Custom_Logger as Custom_Logger, logging, helpers.Manufacturing_Info as Manufacturing_Info, helpers.Power_And_AT_Tests as Power_And_AT_Tests, helpers.labels.Generate_MicroEdge_Labels as Generate_MicroEdge_Labels
import sys, shutil, time, helpers.AT_Commands_ME as AT_Commands_ME
from termcolor import *
from productsdb import products
import pyvisa as visa

with open('configs/test_env.json', 'r') as config_file:
    config = json.load(config_file)

#AT_Commands_ME.initialize_me()
products.init_db_path(config["db_path"])
STM_CLI_PATH = config["STM_CLI_PATH"]
FLASH_IMAGE_PATH = config["FLASH_IMAGE_PATH"]

local_test_path = config["local_test_path"]
make = config["make"]
model = config["model"]
variant = config["variant"]

# Open a connection to the Rigol DP832 power supply
rm = visa.ResourceManager() 
usb_resource = "USB0::0x1AB1::0x0E11::DP8C204204520::INSTR"
power_supply = rm.open_resource(usb_resource)
power_supply.write("OUTP CH2, ON")
power_supply.write(f"APPL CH2, 3.8,{0.5}")
power_supply.write("OUTP CH1, ON")
power_supply.write(f"APPL CH1, 3.8,{0.5}")

Custom_Logger.create_logger('output.txt')  # Set up the custom logging configuration

# Check if argument not to print has been passed in the terminal
print_flag = ''
if len(sys.argv) > 1 and print_flag == '':
    if sys.argv[1] == '--no-print':
        print_flag = sys.argv[1]

technician, hardware_version, batch_id, manufacturing_order = None, None, None, None

ALL_TESTS = ['LoraPush', 'DipSwitches', 'Voltage', 'Pulses', 'LoraReceive', 'FactoryReset']

def all_tests_passed(strings, target_string):
    return all(string in target_string for string in strings)

def run_subprocess(command):
    try:
        with open('lora_info.txt', 'w') as output_file:
            process = subprocess.Popen(command, shell=False, stdout=output_file, stderr=subprocess.STDOUT, text=True)

            # Wait for the process to finish
            #process.wait()

            # Log the process return code
            #logging.info(f"Subprocess finished with return code: {process.returncode}")

    except Exception as e:
        logging.error(f"An error occurred: {e}. The LoRa Receiver seems to be disconnected.")

first_run = True

while True:
    comments = ''
    #make sure the test output file is clean for each device
    with open('output.txt', "w") as file:
        file.truncate(0)
    with open('lora_info.txt', "w") as file:
        file.truncate(0)

    # Check if technician and info is still the same
    if None not in (technician, hardware_version, batch_id, manufacturing_order):
        input(colored('Press rst+boot buttons on device and Press ENTER to execute the script to flash and test.\n', 'white', 'on_blue'))
        technician, hardware_version, batch_id, manufacturing_order = Manufacturing_Info.current_technician_and_info(technician, hardware_version, batch_id, manufacturing_order)
    else:
        # First execution of script, get technician and info
        technician, hardware_version, batch_id, manufacturing_order = Manufacturing_Info.current_technician_and_info()
        input(colored('Press rst+boot buttons on device and Press ENTER to execute the script to flash and test.\n', 'white', 'on_blue'))
    if(first_run):
        run_subprocess(["pyserial-miniterm", "/dev/ttyUSB0", "38400"])
        first_run = False
    # Delete all data on the Pi to make sure it is ready to be flashed
    subprocess.run(["sudo", STM_CLI_PATH, "-c", "port=usb1", "-e", "all"])
    
    logging.info(colored("Pi succesfully prepared for flashing.\n", 'white', 'on_blue'))

    return_code = 1
    # Flash
    while return_code == 1:
        process_info = subprocess.run(["sudo", STM_CLI_PATH, "-c", "port=usb1", "-d", FLASH_IMAGE_PATH, "0x08000000"])
        return_code = process_info.returncode
        if(return_code == 1):
            input(colored('Flashing Unsuccessful. Make sure to press the rst+boot buttons to enable flashing and press ENTER.\n', 'white', 'on_blue'))
    logging.info(colored(f"Pi succesfully flashed.\n", 'white', 'on_blue'))

    # Reboot
    subprocess.run(["sudo", STM_CLI_PATH, "-c", "port=usb1", "-g"])

    print('Rebooting system...\n')
    time.sleep(4)

    input(colored("press Reset button on ME and Press ENTER to test device\n", 'white', 'on_blue'))
    # power_supply.write("OUTP CH2, OFF")
    time.sleep(2)
    #AT_Commands_ME.initialize_me()
    # power_supply.write("OUTP CH2, ON")
    # power_supply.write(f"APPL CH2,3.8,{0.5}")
    #time.sleep(10)

    logging.info(colored("Started tests.\n", 'white', 'on_blue'))

    # Test Voltage and Current 
    loraID, fw_version, hw_version, unique_id, comments = Power_And_AT_Tests.main(power_supply, make, model, variant)

    # Read the content of the file to check for the test signal sent from our sending device ()
    with open("lora_info.txt", "r") as file:
        file_content = file.read()

    # Search for the string in the content
    sending_device_serial = loraID
    signal_received = sending_device_serial in file_content

    if signal_received:
        logging.info(colored(f"LoRa signal received from test device, module working.", 'white', 'on_green'))
        comments += 'LoraReceive,'
    else:
        logging.info(colored(f"Failed - LoRa signal not received from test device.", 'white', 'on_red'))

    factory_reset = AT_Commands_ME.command(b'FACTORYRESET')
    print(colored('Performing a factory reset to erase test values from ME...', 'white', 'on_blue'))
    time.sleep(2)

    pulse_number = AT_Commands_ME.data_pulsesCounter()
    if(factory_reset == 'OK' and pulse_number == 0):
        logging.info(colored(f"Working - Device fully reset, test completed successfully.\n", "white", "on_green"))
        comments += 'FactoryReset'
    else:
        logging.info(colored(f"Failed - Factory reset incomplete, pulse numbers at: {int(pulse_number)}.\n", "white", "on_red"))

    barcode = ''
    barcode = products.get_products_by_loraid(loraID)

    if not barcode:
        barcode = ''

    if(all_tests_passed(ALL_TESTS, comments)):
        if(barcode == ''):
            # new product
            barcode = products.add_product(manufacturing_order, make, model, variant, loraID, unique_id, hardware_version, batch_id,
                fw_version, technician, True, comments)
        # barcode found so just update the already existing product in the db
        else:
            barcode = products.update_product(manufacturing_order, barcode, unique_id, hardware_version, batch_id,
                fw_version, technician, True, comments)
    else:
        print(colored('Full test suite failed, follow next steps to retry.', 'white', 'on_red'))
        continue
    # Copy the contents of the old file to the new file
    shutil.copyfile('output.txt', f"{local_test_path}{barcode}.txt")

    Generate_MicroEdge_Labels.main(barcode, make, model, variant, hw_version, fw_version, batch_id, print_flag)


