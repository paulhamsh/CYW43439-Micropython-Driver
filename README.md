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

The SPI interface is unusual. This is explained well here https://iosoft.blog/2022/12/06/picowi/ and results writes being clocked on the falling clock edge, and reads being clocked on the rising clock edge.    
This is problematic on the first read bit in the word, because the SoftSPI class in Micropython misses the need to read as the clock rises. I can't find a way to get the read to pick up that first bit.    
This manifests in a read of the FEEDBEAD (which is BEADFEED in 32 bit LE) picking up 7D5BFDDA, which is the same value missing the first bit.   

Also the Soft SPI expects different pins for MOSI and MISO, and the class sets MISO last - resulting in the pin being set to input and therefore unable to write any data at all.    
This code handles that, and picks up the first bit, but will require a shift of that bit into the other read bytes.   
```
cs.value(0)
    spi = SoftSPI(baudrate=10000000, polarity=0, phase=0, sck=Pin(29), mosi=Pin(24), miso=Pin(4))
    spi.write(w)
    data_pin = Pin(24, Pin.IN)
    bit = data_pin.value()  # read that first bit which SoftSPI will miss
    spi = SoftSPI(baudrate=1000000, polarity=1, phase=1, sck=Pin(29), mosi=Pin(24), miso=Pin(24))
    read = spi.read(20)     # read the other bits - but remember this is now mis-aligned
```
