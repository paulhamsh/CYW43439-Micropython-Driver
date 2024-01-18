# CYW43439-Micropython-Driver
**A driver for CYW43439 (Pico Pi W) completely in Micropython**

Collated from information found on google and in a variety of repositories on github.   
All code is original based on these sources.  
Also includes some investigatory work on how access to the CWY43439 works from the SPI layer up.  

Really useful sources. 
Most only talk about getting WIFI to work, and bluetooth is an additional set of code.   

```
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
```


