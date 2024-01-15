
#  MicroEdge Manufacturing

This README provides instructions on how to set up and run flashing and testing processes for MicroEdge products.

Documentation for Testing and Flashing MicroEdges:

https://docs.google.com/document/d/15nvyE7ae9OLtkdCV-5EW5XxLy7rBOZ0Jv1tyARIeYv8/edit

## Prerequisites

1. **Python**: Ensure you have Python installed on your local and remote machines. This code was written in Python 3.

2. **Install needed packages**:

Make sure to install all dependencies by running the command below:

```bash
pip install -r requirements.txt
```

### Setting Up

Before running the diagnostic tool, you should have the following set up:

1. **LoRa Receiver for LoRa Testing**: Ensure you have a LoRa Receivber connected to the computer via a USB Type A to Type Mini-B cable, ensuring it is connected to power. Usually on a Linux based system it will connect to a usb port such as ttyUSB0, which is the one used by default in the script. In case an error appears on execution noting the LoRa Receiver seems to be disconnected, make sure to verify it is correctly connected and that it actually appears in the list of connected devices, or if it is connected to a different usb port. (ex: open a terminal, use cd /dev/ and ls. Disconnect and connect cable and check what usb port the LoRa Receiver is on).

2. **Connect the MicroEdge**: Connect the device to be tested as provided in the pdf documentation (top of README file). 

3. **Ensure correct config file setup**: In the config folder you find  the prod and test env json files, these have relevant config values that you might need to set depending on what device type you are manufacturing/testing, and what path your STM software/Flash image occupy on your machine. 

In the main Flash_And_test.py script, you can change between a production and test envrionment by loading in the correct json file at the top.

For code development, use the test_env.json file, to ensure not poluting the production database.

## Flashing and Testing 

1. **Execute flash and test script**: To flash and test a device from scrap use:

```bash
sudo python3 Flash_And_Test.py
```

   In case you don't need to print barcode labels you can use the --no-print option as follows:

 ```bash
sudo python3 Flash_And_Test.py --no-print
```
2. **Testing only**:

If only checking for a MicroEdge's health use:
 ```bash
sudo python3 Check_ME.py
```

The terminal will show valuable information regarding the MicroEdge's state.

## AT-Command Guide

The below shows how AT commands are constructed and lists out what commands are currently available.

1. Begin:
- `AT+`

The MCU will continually wait until it reads these three characters consecutively and discard anything else.

2. Structure:
- `AT+<command><type><data>`

Commands are completed with a newline character (`\n`)
Carrige returns (`\r`) and other typical modifier chars are ignored

Any data entered will be stored for (`10`)seconds from the last received character so commands can be manually entered if needed.

Return data will follow two structures depending on return type (ended by newlines):
- `+<command>:<data>`
- `OK` or `ERROR`

3. Command Types:
- `?` - Query
- `=` - Set
- ``  - Execute (no type, only command)

The AT command interface needs to be unlocked with `UNLOCK` command before invoking any Set or Execute commands.


4. General Commands

|       Desc            |       Command         |                       Return                              |
|---                    |---                    |---                                                        |
|Firmware Version       |AT+FWVERSION?          |+FWVERSION:&lt;major&gt;.&lt;minor&gt;.&lt;patch&gt;[-&lt;pre-release&gt;]<br/>+FWVERSION:4.0.0<br/>+FWVERSION:4.0.0-1|
|HW Version             |AT+HWVERSION?          |+HWVERSION: &lt;major&gt;.&lt;minor&gt;<br/>+HWVERSION: 0.1|
|                       |AT+HWVERSION=&lt;major&gt;.&lt;minor&gt;|OK<br/>ERROR|
|STM32 96-bit Unique ID |AT+UNIQUEID?           |+UNIQUEID:&lt;24-char-hex-string&gt;<br/>+UNIQUEID:0123456789ABCDEF01234567|
|Device Make            |AT+DEVICEMAKE?         |+DEVICEMAKE: &lt;device make 2 bytes&gt;<br/>+DEVICEMAKE: ME|
|Device Model           |AT+DEVICEMODEL?        |+DEVICEMODEL: &lt;device model 4 bytes&gt;<br/>+DEVICEMODEL: 0005|
|Soft Reset             |AT+SOFTRESET           |OK<br/>ERROR                                               |
|Factory Reset          |AT+FACTORYRESET        |OK<br/>ERROR                                               |
|**Device Security**    |                       |                                                           |
|LOCK                   |AT+LOCK?               |+LOCK:&lt;state&gt;<br/>+LOCK: 0 (unlocked)<br/>+LOCK: 1 (locked)|
|                       |AT+LOCK=&lt;password&gt;<br/>|OK<br/>ERROR            |
|UNLOCK                 |AT+UNLOCK?             |+UNLOCK:&lt;state&gt;<br/>+UNLOCK: 0 (locked)<br/>+UNLOCK: 1 (unlocked)|
|                       |AT+UNLOCK=&lt;password&gt;<br/><br/>Unlocking is temporary. The device will be relocked on resetting or 30 minutes after unlocking|OK<br/>ERROR          |
|Password               |AT+PASSWORD=&lt;current password&gt;,&lt;new password&gt;<br/>maximum password length is 32|OK<br/>ERROR            |
|Bootloader             |AT+ENTERBOOTLOADER     |OK<br/>ERROR                                               |

5. LoRa Commands

|       Desc            |         Command       |                           Return                          |
|---                    |---                    |---                                                        |
|Unique address         |AT+LRRADDRUNQ?         |+LORAADDRUNQ:&lt;lora-raw-address&gt;<br/>+LORAADDUNQ:00C01234|
|Lora detect            |AT+LORADETECT?         |+LORADETECT:&lt;lora-detect <0 or 1>&gt;<br/>+LORADETECT:0 |
|Push a LoRaRaw packet  |AT+LORARAWPUSH         |OK<br/>ERROR                                               |

6. Device data commands

|       Desc            |         Command       |                           Return                          |
|---                    |---                    |---                                                        |
|Battery voltage        |AT+VALUE_VBAT?         |+VALUE_VBAT:&lt;voltage&gt; or<br/>ERROR<br/>+VALUE_VBAT: 4.63|
|Pulses Counter         |AT+VALUE_PULSE?        |+VALUE_PULSE:&lt;pulses counter&gt; or<br/>ERROR<br/>+VALUE_PULSE: 1234|
|DIP Switches           |AT+VALUE_DIPSWITCHES?  |+VALUE_DIPSWITCHES:&lt;Dipswitches value&gt;<br/>+VALUE_DIPSWITCHES: [0,0,1,0,0,1,0,1]|
|Normalized voltage of AIN 1|AT+VALUE_UI1_RAW? |+VALUE_UI1_RAW:&lt;normalized voltage&gt; or<br/>ERROR<br/>+VALUE_UI1_RAW: 0.42|
|Normalized voltage of AIN 2|AT+VALUE_UI2_RAW? |+VALUE_UI2_RAW:&lt;normalized voltage&gt; or<br/>ERROR<br/>+VALUE_UI2_RAW: 0.00|
|Normalized voltage of AIN 3|AT+VALUE_UI3_RAW? |+VALUE_UI3_RAW:&lt;normalized voltage&gt; or<br/>ERROR<br/>+VALUE_UI3_RAW: 1.00|
