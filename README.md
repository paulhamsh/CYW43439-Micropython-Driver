# CYW43439-Micropython-Driver
## A driver for CYW43439 (Pico Pi W) completely in Micropython

## Overview
This is a basic HCI BLE capability for the Pico Pi W. It is all in Micropython - both the BLE HCI layer and the driver for the CYW43439 WIFI/BT chip.   
There is no reliance on any bluetooth stack or CWY43439 driver.    
It is a bit slow to load up all the firmware.    
It is BLE only, no other bluetooth and no WIFI - written solely to prove the BLE HCI capability.   
Run the ```test.py``` program with one of the three options: 
```
ble.conn()
ble.adv()
ble.test()
```

```ble.conn()``` looks for a device with address D8:3A:DD:41:84:51 - change this to an address of your device. It also expects that device to send data.   Example code for that is in ```test```.   




## Sources
Collated from information found on google and in a variety of repositories on github.   
All code is original based on these sources.  
Also includes some investigatory work on how access to the CWY43439 works from the SPI layer up.  

Really useful sources. 
Most only talk about getting WIFI to work, and bluetooth is an additional set of code.   

Infineon data sheet
https://www.infineon.com/dgdl/Infineon-CYW43439-DataSheet-v05_00-EN.pdf?fileId=8ac78c8c8929aa4d01893ee30e391f7a    
or from here via 'download' button     
https://www.infineon.com/cms/en/product/wireless-connectivity/airoc-wi-fi-plus-bluetooth-combos/wi-fi-4-802.11n/cyw43439/    

Code     
Pico SDK C  https://github.com/raspberrypi/pico-sdk/tree/master/src/rp2_common/pico_cyw43_driver     
Rust        https://github.com/embassy-rs/embassy/tree/main/cyw43     
Go          https://github.com/soypat/cyw43439     

Documents
https://iosoft.blog/2022/12/06/picowi/     

Information about the firmware
https://github.com/georgerobotics/cyw43-driver/tree/main/firmware     


Not only is the communication between the Pico and the CYW43439 a challenge, getting the CYW434349 programmed and running is complex.   
The chip needs to be programmed with WIFI firmware, then some nvram settings and then the bluetooth firmware (which is in an interestingly complex format).   
(Luckily it seems the CLM database may not be needed for bluetooth operation)    

Much isn't documented so is based on code in the other drivers.   

## SPI timings

The SPI interface is unusual in the setup most code uses - referre to as HICH_SPEED mode. This is explained well here https://iosoft.blog/2022/12/06/picowi/   and shown in the timing chart below.    

<p align="center">
  <img src="https://github.com/paulhamsh/CYW43439-Micropython-Driver/blob/main/CYW Timing High Speed.jpg" width="700" title="Timings">
</p>

<p align="center">
  <img src="https://github.com/paulhamsh/CYW43439-Micropython-Driver/blob/main/CYW Timing Normal Speed.jpg" width="700" title="Timings">
</p>


Write data is put on the bus to be read by the CYW on the rising clock edge.       
Data from the CYW is read on the falling clock edge.   
This is problematic on the first read bit in the word, because the SoftSPI class in Micropython misses the need to read the first bit as the clock falls. I can't find a way to get the read to pick up that first bit but it can be done manually, and then the whole resulting bytes shifed one bit to the right to accomodate this. Which is slow.    
This manifests in a read of the FEEDBEAD (which is BEADFEED in 32 bit LE) picking up 7D5BFDDA, which is the same value missing the first bit.   

But, if the start-up sequence is changed to set this without HIGH_SPEED as the second instruction, before the FEEDBEAD check, then normal SPI works.   
So I have changed the start-up to be a dummy write (to clear the 4 bits of data that get added to any first read), then setting the configuration register.   
This also removed the need for any further 'swap' caused by little endian / big endian changes.   

```
    # Send empty bytes to clear 4-bit buffer
    read = spi_transfer(b'\x00', 1, 0)  # Just to clear the 4bit extra needed
    
    # Set configuration
    config = WORD_LENGTH_32 | BIG_ENDIAN | INT_POLARITY_HIGH | WAKE_UP | INTR_WITH_STATUS  #  Not HIGH_SPEED
    cyw_write_reg_u32_swap(SPI_FUNC, CONFIG_REG, config)

    # Try to read FEEDBEAD
    read = cyw_read_reg_u32(SPI_FUNC, FEEDBEAD_REG)
    print_hex_val_u32("---- SPI transfer read", read)
```

Also the Soft SPI expects different pins for MOSI and MISO, and the class sets MISO last - resulting in the pin being set to input and therefore unable to write any data at all.    

The SPI code (https://github.com/micropython/micropython/blob/master/drivers/bus/softspi.c) does this

```
case MP_SPI_IOCTL_INIT:
    mp_hal_pin_write(self->sck, self->polarity);
    mp_hal_pin_output(self->sck);
    mp_hal_pin_output(self->mosi);
    mp_hal_pin_input(self->miso);
    break;
```

So will change the clock value and ensure that MISO is an input.

This code manually sets the Pin directions and therefore works fine, once HIGH_SPEED mode is removed.   
```
def spi_transfer_softSPI(write, write_length, read_length):
    cs.value(0)
    spi = SoftSPI(baudrate=50000000, polarity=0, phase=0, sck=Pin(29), mosi=Pin(24), miso=Pin(24))
    data_pin = Pin(24, Pin.OUT)  # because constructor makes it IN as its last IOCTL action
    spi.write(write)
    
    new_read = b''
    if read_length > 0:
        data_pin = Pin(24, Pin.IN)
        new_read = spi.read(read_length)
        
    cs.value(1)
    return bytes(new_read)
```

## Sample HCI logging output

For the ble.conn() example in ble.py
```
---- SPI transfer read   				Value u32:  0xFEEDBEAD
---- Core WLAN in reset
---- Core SOCSRAM in reset
---- Chip id: 43439
.... Failed HT clock
Bluetooth firmware version: CYW4343A2_001.003.016.0031.0000_Generic_SDIO_37MHz_wlbga_BU_dl_signed
Number of records 33
BT not ready yet
WIFI Base                				Value u32:  0x0006861C

<< Command: LE Set Scan Disable

<< Data sent:  01 0c 20 02 00 00

>> Data received:  04 0e 04 01 0c 20 0c
Packet type: 4
HCI Event Packet: 0xe
Event: HCI Command Complete
LE Scan Enable Set: Failure

<< Command: LE Add Device To Filter Accept List

<< Data sent:  01 11 20 07 00 51 84 41 dd 3a d8

>> Data received:  04 0e 04 01 11 20 00
Packet type: 4
HCI Event Packet: 0xe
Event: HCI Command Complete
LE Unknown Command: 0x2011 Success

<< Command: LE Set Scan Parameters

<< Data sent:  01 0b 20 07 01 60 00 60 00 00 00

>> Data received:  04 0e 04 01 0b 20 00
Packet type: 4
HCI Event Packet: 0xe
Event: HCI Command Complete
LE Scan Parameters Set: Success

<< Command: LE Set Scan Enable

<< Data sent:  01 0c 20 02 01 01

>> Data received:  04 0e 04 01 0c 20 00
Packet type: 4
HCI Event Packet: 0xe
Event: HCI Command Complete
LE Scan Enable Set: Success

>> Data received:  04 3e 2b 02 01 00 00 51 84 41 dd 3a d8 1f 02 01 06 09 09 50 69 63 6f 4d 69 64 69 11 07 00 c7 c4 4e e3 6c 51 a7 33 4b e8 ed 5a 0e b8 03 d9
Packet type: 4
HCI Event Packet: 0x3e
Event: LE Meta event:  0x2
Address: d8:3a:dd:41:84:51      RSSI: 217
Length:   2 Type: 01  Data: 06      .
Length:   9 Type: 09  Data: 50 69 63 6f 4d 69 64 69      PicoMidi
Length:  17 Type: 07  Data: 00 c7 c4 4e e3 6c 51 a7 33 4b e8 ed 5a 0e b8 03      ...N.lQ.3K..Z...

<< Command: LE Set Scan Disable

<< Data sent:  01 0c 20 02 00 00

>> Data received:  04 0e 04 01 0c 20 00
Packet type: 4
HCI Event Packet: 0xe
Event: HCI Command Complete
LE Scan Enable Set: Success

<< Command: LE Create Connection

<< Data sent:  01 0d 20 19 60 00 60 00 00 00 51 84 41 dd 3a d8 00 18 00 28 00 00 00 2a 00 00 00 00 00

>> Data received:  04 0f 04 00 01 0d 20
Packet type: 4
HCI Event Packet: 0xf
Event: HCI Command Status
Opcode: 200d status: 00

>> Data received:  04 3e 13 01 00 40 00 00 00 51 84 41 dd 3a d8 27 00 00 00 2a 00 00
Packet type: 4
HCI Event Packet: 0x3e
Event: LE Meta event:  0x1
LE Connection Complete
Status: 00 Address: d8:3a:dd:41:84:51

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

<< Command: LE Read Remote Features

<< Data sent:  01 16 20 02 40 00

>> Data received:  04 0f 04 00 01 16 20
Packet type: 4
HCI Event Packet: 0xf
Event: HCI Command Status
Opcode: 2016 status: 00

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

<< LE Command:  ATT EXCHANGE MTU REQ

<< Data sent:  02 40 00 07 00 03 00 04 00 02 05 02

>> Data received:  02 40 20 07 00 03 00 04 00 03 05 02
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 7 Data size: 3 Full packet? True
ACL packet:     03 05 02
ACL data:       03 05 02

>> Data received:  04 13 05 01 40 00 01 00
Packet type: 4
HCI Event Packet: 0x13
Event: HCI Number Of Completed Packets

<< LE Command:  ATT READ BY TYPE REQ

<< Data sent:  02 40 00 0b 00 07 00 04 00 08 01 00 ff ff 00 28

>> Data received:  02 40 20 0e 00 0a 00 04 00 09 04 01 00 00 18 04 00 01 18
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 14 Data size: 10 Full packet? True
ACL packet:     09 04 01 00 00 18 04 00 01 18
ACL data:       09 04 01 00 00 18 04 00 01 18

>> Data received:  04 13 05 01 40 00 01 00
Packet type: 4
HCI Event Packet: 0x13
Event: HCI Number Of Completed Packets

<< LE Command:  ATT FIND INFORMATION REQ

<< Data sent:  02 40 00 09 00 05 00 04 00 04 01 00 ff ff

>> Data received:  02 40 20 1b 00 22 00 04 00 05 01 01 00 00 28 02 00 03 28 03 00 00 2a 04 00 00 28 05 00 03 28 06
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 27 Data size: 34 Full packet? False
ACL packet:     05 01 01 00 00 28 02 00 03 28 03 00 00 2a 04 00 00 28 05 00 03 28 06

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

<< LE Command:  ATT FIND INFORMATION REQ

<< Data sent:  02 40 00 09 00 05 00 04 00 04 09 00 ff ff

>> Data received:  02 40 20 18 00 14 00 04 00 05 02 09 00 f3 6b 10 9d 66 f2 a9 a1 12 41 68 38 db e5 72 77
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 24 Data size: 20 Full packet? True
ACL packet:     05 02 09 00 f3 6b 10 9d 66 f2 a9 a1 12 41 68 38 db e5 72 77
ACL data:       05 02 09 00 f3 6b 10 9d 66 f2 a9 a1 12 41 68 38 db e5 72 77

>> Data received:  04 13 05 01 40 00 01 00
Packet type: 4
HCI Event Packet: 0x13
Event: HCI Number Of Completed Packets

<< LE Command:  ATT FIND INFORMATION REQ

<< Data sent:  02 40 00 09 00 05 00 04 00 04 0a 00 ff ff

>> Data received:  02 40 20 0a 00 06 00 04 00 05 01 0a 00 02 29
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 10 Data size: 6 Full packet? True
ACL packet:     05 01 0a 00 02 29
ACL data:       05 01 0a 00 02 29

>> Data received:  04 13 05 01 40 00 01 00
Packet type: 4
HCI Event Packet: 0x13
Event: HCI Number Of Completed Packets

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

<< LE Command:  ATT FIND INFORMATION REQ

<< Data sent:  02 40 00 09 00 05 00 04 00 04 0b 00 ff ff

>> Data received:  02 40 20 09 00 05 00 04 00 01 04 0b 00 0a
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 9 Data size: 5 Full packet? True
ACL packet:     01 04 0b 00 0a
ACL data:       01 04 0b 00 0a

>> Data received:  04 13 05 01 40 00 01 00
Packet type: 4
HCI Event Packet: 0x13
Event: HCI Number Of Completed Packets

<< LE Command:  ATT READ REQ

<< Data sent:  02 40 00 07 00 03 00 04 00 0a 09 00

>> Data received:  02 40 20 0a 00 06 00 04 00 0b 80 80 b0 10 7f
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 10 Data size: 6 Full packet? True
ACL packet:     0b 80 80 b0 10 7f
ACL data:       0b 80 80 b0 10 7f

>> Data received:  04 13 05 01 40 00 01 00
Packet type: 4
HCI Event Packet: 0x13
Event: HCI Number Of Completed Packets

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00

>> Data received:  02 40 20 0c 00 08 00 04 00 1b 09 00 80 80 b0 10 00
Packet type: 2
ACL Packet
ACL header: handle: 64  bc: 0  pb: 2
Channel: 4 Length: 12 Data size: 8 Full packet? True
ACL packet:     1b 09 00 80 80 b0 10 00
ACL data:       1b 09 00 80 80 b0 10 00
DONE
>>>
```

    

