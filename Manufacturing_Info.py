import keyboard
import re
import logging
from datetime import datetime
from termcolor import *

# Technician name and manufacturing info to be recorded
technician = ''
hardware_version = ''
batch_id = ''
manufacturing_order = ''

def format_batch_id(batch):
    global batch_id

    # Define the regex pattern
    regex = r"^(?:\d{2}\d{2}|[0-4]\d-\d{2}-\d{2})$"

    if not re.match(regex, batch) and (len(batch) != 4 or len(batch) != 8):
        print(colored('Batch has to be one of the following formats: YYWW (ex:2320) or YY-MM-DD (ex: 23-07-31)\n', 'white', 'on_red'))
    
    # Check if it's in the "YY-MM-DD" format and convert it
    if len(batch) == 8:
        try:
            date_obj = datetime.strptime(batch, "%y-%m-%d")
            batch = date_obj.strftime('%y%W')
        except ValueError:
            print("Invalid date format in YY-MM-DD.")

    # Check WW is between 01 and 52
    if len(batch) == 4:
        year = int(batch[:2])
        week = int(batch[2:])

    current_year = datetime.now().year % 100  # Get the last 2 digits of the current year

    # range doesnt include the upper limit so we add +1 to it to include the current year
    valid_year_range = range(current_year - 5, current_year + 1)

    if year not in valid_year_range or week < 1 or week > 52:
        print(colored('Batch needs a valid week between 1 and 52, and a year within a 5 year range\n', 'white', 'on_red'))
        return False

    batch_id = batch
    return batch

def get_valid_input(prompt, regex=None):
    global batch_id

    while True:
        user_input = input(colored(prompt, 'white', 'on_blue'))

        if regex and not re.match(regex, user_input):
            if regex == r"^[A-Za-z\s]+$":
                # Name input wrong
                print(colored('Name has to contain spaces and letters only\n', 'white', 'on_red'))
            elif regex == r"^(v?\d{0,2}\.\d{0,2})$":
                # Hardware input wrong
                print(colored('Hardware has to be a number with up to 2 digits and 2 decimals, examples: 1.0 | 15.23\n', 'white', 'on_red'))
            elif regex == r"^(?:\d{2}\d{2}|[0-4]\d-\d{2}-\d{2})$":
                # Date input wrong
                print(colored('Batch has to be one of the following formats: YYWW (ex: 2320) or YY-MM-DD (ex: 23-07-31)\n', 'white', 'on_red'))
            continue
        if regex == r"^(?:\d{2}\d{2}|[0-4]\d-\d{2}-\d{2})$":
            result = format_batch_id(user_input)
            if result is False:
                # Re-enter batch_id for both "YYWW" and "YY-MM-DD" formats
                batch_id = get_valid_input("*** Please enter the batch_id in the form of YYWW (ex:2320) or YY-MM-DD (ex: 23-07-31) and press ENTER ***\n", regex=r"^(?:\d{2}\d{2}|[0-4]\d-\d{2}-\d{2})$")
            else:
                return result
        #check if hardware version has a v
        elif regex == r"^(v?\d{0,2}\.\d{0,2})$":
            return user_input.lstrip('v')  
        return user_input

def current_technician_and_info(saved_technician = None, saved_hardware_version = None, saved_batch_id = None, saved_manufacturing_order = None):
    global technician, hardware_version, batch_id, manufacturing_order

    technician = ''
    hardware_version = ''
    batch_id = ''
    manufacturing_order = ''


    if (saved_technician and saved_hardware_version and saved_batch_id and saved_manufacturing_order):
        technician = saved_technician
        hardware_version = saved_hardware_version
        batch_id = saved_batch_id
        manufacturing_order = saved_manufacturing_order

    if (technician and hardware_version and batch_id and manufacturing_order):
        print(colored(f"Tester: {technician}\nHardware Version: {hardware_version}\nBatch: {batch_id}\nWork Order: {manufacturing_order}\n", 'black', 'on_yellow'))
        print(colored("*** If the info is still correct, press y. If you need to reenter it, press n ***\n", 'white', 'on_blue'))
        while True:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == 'y':
                    keyboard.press_and_release('backspace')
                    logging.info(colored(f"Tester: {technician}\nHardware Version: {hardware_version}\nBatch: {batch_id}\nWork Order: {manufacturing_order}", 'black', 'on_yellow'))

                    return technician, hardware_version, batch_id, manufacturing_order
                elif event.name == 'n':
                    keyboard.press_and_release('backspace')
                    break

    technician = get_valid_input("*** Please enter your name and press ENTER ***\n", regex=r"^[A-Za-z\s]+$").title()
    hardware_version = get_valid_input("*** Please enter the hardware version and press ENTER ***\n", regex=r"^(v?\d{0,2}\.\d{0,2})$")
    get_valid_input("*** Please enter the batch_id in the form of YYWW (ex:2320) or YY-MM-DD (ex: 23-07-31) and press ENTER ***\n", regex=r"^(?:\d{2}\d{2}|[0-4]\d-\d{2}-\d{2})$")
    while True:
        manufacturing_order = get_valid_input("*** Please enter the work order serial and press ENTER ***\n").upper()
        if re.match(r"^MO\d{5}$", manufacturing_order):
            break
        else:
            print(colored('Work Order should start with "MO" followed by 5 digits (ex: MO00025). \n', 'white', 'on_red'))
    logging.info(colored(f"Tester: {technician}\nHardware Version: {hardware_version}\nBatch: {batch_id}\nWork Order: {manufacturing_order}", 'black', 'on_yellow'))

    return technician, hardware_version, batch_id, manufacturing_order