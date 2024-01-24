# CYW43439-Micropython-Driver
## A driver for CYW43439 (Pico Pi W) completely in Micropython

Collated from information found on google and in a variety of repositories on github.   
All code is original based on these sources.  
Also includes some investigatory work on how access to the CWY43439 works from the SPI layer up.  


## Sources
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

    

