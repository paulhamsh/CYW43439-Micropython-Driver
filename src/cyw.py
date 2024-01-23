from machine import Pin
from time import sleep_ms, sleep_us
import rp2

cs  = Pin(25, Pin.OUT)
clk = Pin(29, Pin.OUT)
pwr = Pin(23, Pin.OUT)

TIMING_DELAY = 1

# Constants for WIFI chip

# gSPI command structure (CW43439 Datasheet 002-30348 Rev *B page 19)

SPI_FUNC  = 0
BACK_FUNC = 1

# Cores
CORE_WLAN    = 1
CORE_SOCSRAM = 2

# gSPI
#
# Registers (CW43439 Datasheet 002-30348 Rev *B page 22)

CONFIG_REG               = 0x00
SPI_INT_REG              = 0x04
SPI_INT_ENABLE_REG       = 0x06
SPI_STATUS_REG           = 0x08
FEEDBEAD_REG             = 0x14
TEST_REG                 = 0x18
BACKPLANE_PAD_REG        = 0x1d

# Config register values

WORD_LENGTH_32           = 0x0000_0001
BIG_ENDIAN               = 0x0000_0002
HIGH_SPEED               = 0x0000_0010
INT_POLARITY_HIGH        = 0x0000_0020
WAKE_UP                  = 0x0000_0080
STATUS_ENABLE            = 0x0001_0000
INTR_WITH_STATUS         = 0x0002_0000

# Interrupt register values - these aren't fully described in the specification

DATA_UNAVAILABLE         = 0x0001
COMMAND_ERROR            = 0x0008
DATA_ERROR               = 0x0010
F1_OVERFLOW              = 0x0080

# Interrupt enable values

F2_F3_FIFO_RD_UNDERFLOW  = 0x0002
F2_F3_FIFO_WR_OVERFLOW   = 0x0004
COMMAND_ERROR            = 0x0008
DATA_ERROR               = 0x0010
F2_PACKET_AVAILABLE      = 0x0020
F1_OVERFLOW              = 0x0080
F1_INTR                  = 0x2000

# Pad register value

BACKPLANE_PAD_VALUE      = 0x04

# Status register values

STATUS_F2_RX_READY       = 0x0000_0020

# BACKPLANE REGISTERS
#
# Backplane registers

SDIO_FUNCTION2_WATERMARK = 0x1_0008 
BACKPLANE_LOW_REG        = 0x1_000a
BACKPLANE_MED_REG        = 0x1_000b
BACKPLANE_HIGH_REG       = 0x1_000c
SDIO_CHIP_CLOCK_CSR      = 0x1_000e
SDIO_PULL_UP             = 0x1_000f

# ALP Clock

SBSDIO_ALP_AVAIL_REQ     = 0x08
SBSDIO_ALP_AVAIL         = 0x40
SBSDIO_HT_AVAIL          = 0x80

# Backplane registers
WLAN_BASE_ADDRESS_REG    = 0x1800_0d68
HOST_CONTROL_REG         = 0x1800_0d6c
BT_CONTROL_REG           = 0x1800_0c7c

# Host control register values
WAKE_BT                  = 0x0002_0000
DATA_VALID               = 0x0000_0002
SW_READY                 = 0x0100_0000

# BT control register values
BT_AWAKE                 = 0x0000_0100
FW_READY                 = 0x0100_0000


# BACKPLANE ADDRESSES
#
# Backplane addresses

CHIPCOMMON_BASE_ADDRESS  = 0x1800_0000
SDIO_BASE_ADDRESS        = 0x1800_2000
WLAN_ARMCM3_BASE_ADDRESS = 0x1800_3000
SOCSRAM_BASE_ADDRESS     = 0x1800_4000

WRAPPER_REGISTER_OFFSET  = 0x10_0000

SBSDIO_SB_ACCESS_2_4B    = 0x8000             # Not sure what this does or if it works

# Core control

AI_IOCTRL_OFFSET         = 0x0408
AI_RESETCTRL_OFFSET      = 0x0800

SICF_CPUHALT             = 0x0020
SICF_FGC                 = 0x0002
SICF_CLOCK_EN            = 0x0001

AIRC_RESET               = 0x0001

# SRAM

SOCSRAM_BANKX_INDEX      = SOCSRAM_BASE_ADDRESS + 0x10
SOCSRAM_BANKX_PDA        = SOCSRAM_BASE_ADDRESS + 0x44

SDIO_INT_HOST_MASK       = SDIO_BASE_ADDRESS + 0x24

I_HMB_SW_MASK            = 0x0000_00f0
I_HMB_FC_CHANGE          = 0x20
SPI_F2_WATERMARK         = 0x20

# Bluetooth - BIT0 => WLAN Power UP and BIT1=> WLAN Wake 

BTFW_MEM_OFFSET          = 0x1900_0000
BT2WLAN_PWRUP_ADDR       = 0x0064_0894
BT2WLAN_PWRUP_WAKE       = 0x03


# HCI buffer pointers - relative to wifi_base

H2BT_BUFFER              = 0x0000
BT2H_BUFFER              = 0x1000

SEND_HEAD                = 0x2000
SEND_TAIL                = 0x2004
RECEIVE_HEAD             = 0x2008
RECEIVE_TAIL             = 0x200c
# SUPPPORTING FUNCTIONS

# Hex printing functions

def print_hex(title, byts):
    if title:
        print('{:25s}'.format(title), end="")
    print("\t\t\t\tMem data:   0x", end="")
    for b in byts:
        print('{0:02X} '.format(b), end = "")
    print()
 
def dump_bytes_hex(address, byts):
    print('{0:08X}'.format(address), end="")
    print("\tMem data: 0x", end="")
    for b in byts:
        print('{0:02X}'.format(b), end = "")
    print("\t", end="")
    for b in byts:
        if b > 126 or b < 32:
            b = 0x2e
        print(chr(b), end = "")    
    print()
    
def print_hexline(title, byts1, byts2):
    '''
    print('{:25s}'.format(title), end="")
    print("Command bytes: 0x", end="")
    for b in byts1:
        print('{0:02X}'.format(b), end = "")
    print("\tData bytes: 0x", end="")
    for b in byts2:
        print('{0:02X}'.format(b), end = "")
    print()
    '''

def print_hex_val_u8(title, val):
    if title:
        print('{:25s}'.format(title), end="")
    print("\t\t\t\tValue u8:   0x", end="")
    print('{0:02X}'.format(val), end = "")
    print() 

def print_hex_val_u16(title, val):
    if title:
        print('{:25s}'.format(title), end="")
    print("\t\t\t\tValue u16:  0x", end="")
    print('{0:04X}'.format(val), end = "")
    print()
    
def print_hex_val_u32(title, val):
    if title:
        print('{:25s}'.format(title), end="")
    print("\t\t\t\tValue u32:  0x", end="")
    print('{0:08X}'.format(val), end = "")
    print() 

# MAIN SPI FUNCTIONS

# Chip power on and off using PWR pin (GPIO 23)

def power_on():
    clk.value(0)
    data_pin=Pin(24, Pin.OUT)
    data_pin.value(0)

    pwr.value(0)
    sleep_ms(20)
    pwr.value(1)
    sleep_ms(250)

def power_off():
    pwr.value(0)

# Core SPI data transmission
'''
from machine import SoftSPI
spi = SoftSPI(baudrate=1000, polarity=1, phase=0, sck=Pin(29), mosi=Pin(24), miso=Pin(24))

def spi_transfer(write, write_length, read_length):
    spi.init(baudrate=1000)
    cs.value(0)
    readbuf = bytearray(read_length)
    spi.write(write[0:write_length])
    if read_length > 0:
        spi.readinto(readbuf)
    cs.value(1)    
    return bytes(readbuf)
'''    
    

def spi_transfer(write, write_length, read_length):
    clk.value(0)
    cs.value(0)
    data_pin = Pin(24, Pin.OUT)
    read = bytearray()  # empty array
   
    for i in range(0, write_length):
        byt = write[i]
        mask = 128
        while mask >= 1:
           bit = 1 if byt & mask else 0
           data_pin.value(bit)
           clk.value(1)
           sleep_us(TIMING_DELAY)
           clk.value(0)
           mask >>= 1
    data_pin = Pin(24, Pin.IN)    

    for i in range(0, read_length):
        byt = 0
        mask = 128
        while mask >= 1:
            bit = data_pin.value()
            byt += mask if bit else 0
            mask >>= 1
            sleep_us(TIMING_DELAY)
            clk.value(1)
            sleep_us(TIMING_DELAY)
            clk.value(0)
        read.append(byt)
    cs.value(1)
    return bytes(read)

# Data conversion and byte swapping
# For swap_words, this changes the ordering from b0 b1 b2 b3 to b1 b0 b3 b2
# So the test register is stored as BE AD FE ED, which is then swapped to AD BE ED FE (bytes)
# As a little-endian value, this is FE ED BE AD which is what we are looking for
# To set the endian value, write 00_01_00_B3 which is B3 00 01 00 in little endian, and changed to 00 B3 00 01 as bytes
# B3 is 1011 0011 which sets wake-up, interrupt polarity high, high speed mode, big endian, 32 bit word
# 01 is 0000 0001 which sets status after read/write and no interrupt if status is sent, the default settings
# TODO - Not sure we want it like that
# Oddly it seems setting the chip to 32 bit big endian is really little endian - with the lowest value byte first

def swap_words(dat):
    return bytes([dat[1], dat[0], dat[3], dat[2]])

def le_bytes_to_u32(le_bytes):
    val = 0
    for b in reversed(le_bytes):
        val <<= 8
        val += b
    return val     
        
def u32_to_le_bytes(int_val):
    b = bytearray()
    for i in range(0, 4):
        b.append(int_val & 0xff)
        int_val >>= 8
    return bytes(b)

def round_to_four(val):
    # adj_val = (val + 3) & ~3       # round u
    return ((val / 4) + 1) * 4

# Function to make the command for gSPI

def make_cmd(wr, inc, fn, addr, size):
    cmd = (wr << 31) | (inc << 30) | (fn << 28) | ((addr & 0x1ffff) << 11) | (size & 0x3ff)
    return cmd

# Register read and write with swap of bytes - for use prior to setting endian
# Used to read the test register (FEEDBEAD) and set the control register and fix the endian value

# Rules on naming
# - if 'reg' in function name then return value is an int
# - if 'bytes' in function name then return value is of type bytes

def cyw_write_reg_u32_swap(fn, addr, val):
    cmd = make_cmd(1, 1, fn, addr & 0x1ffff, 4)
    cmd_bytes = swap_words(u32_to_le_bytes(cmd))
    val_bytes = swap_words(u32_to_le_bytes(val))
    data = cmd_bytes + val_bytes
    spi_transfer(data, 8, 0)
    print_hexline("Write reg swap", cmd_bytes, val_bytes)

def cyw_read_reg_u32_swap(fn, addr):
    cmd = make_cmd(0, 1, fn, addr & 0x1ffff, 4)
    cmd_bytes = swap_words(u32_to_le_bytes(cmd))
    read = spi_transfer(cmd_bytes, 4, 4)
    read_swap = swap_words(read)
    print_hexline("Read reg swap", cmd_bytes, read_swap)
    #return read_swap
    return le_bytes_to_u32(read_swap[0:4])

# Register read functions - base function with length, the u8, u16 and u32 versions

def cyw_read_bytes(fn, addr, length):
    cmd = make_cmd(0, 1, fn, addr & 0x1ffff, length & 0x3ff)
    cmd_bytes = u32_to_le_bytes(cmd)
    pad = BACKPLANE_PAD_VALUE if fn == BACK_FUNC else 0
    length = (length + 3) & ~3
    read = spi_transfer(cmd_bytes, 4, length + pad)
    print_hexline("Read  reg", cmd_bytes, read)
    return read[pad:]

def cyw_write_bytes(fn, addr, val, length):
    cmd = make_cmd(1, 1, fn, addr & 0x1ffff, length & 0x3ff)
    cmd_bytes = u32_to_le_bytes(cmd)
    # the transfer must be a full number of 32 bit words, so pad to the next 4 byte boundary
    adjusted_len = (length + 3) & ~3       # round up
    padding = bytes(adjusted_len - length) # bytes() of this length
    data = cmd_bytes + val + padding
    spi_transfer(data, 4 + (adjusted_len & 0x3ff), 0) # length of transfer is rounded up a word
    print_hexline("Write reg", cmd_bytes, val)

def cyw_read_reg_u8(fn, addr):
    read = cyw_read_bytes(fn, addr, 1)
    return le_bytes_to_u32(read[0:1])

def cyw_read_reg_u16(fn, addr):
    read = cyw_read_bytes(fn, addr, 2)
    return le_bytes_to_u32(read[0:2])

def cyw_read_reg_u32(fn, addr):
    read = cyw_read_bytes(fn, addr, 4)
    return le_bytes_to_u32(read[0:4])

# Register write functions - base function with length, the u8, u16 and u32 versions

def cyw_write_reg_u8(fn, addr, val):
    cyw_write_bytes(fn, addr, u32_to_le_bytes(val), 1)

def cyw_write_reg_u16(fn, addr, val):
    cyw_write_bytes(fn, addr, u32_to_le_bytes(val), 2)
    
def cyw_write_reg_u32(fn, addr, val):
    cyw_write_bytes(fn, addr, u32_to_le_bytes(val), 4)

# Set backplane address (if different from previous value)

backplane_prev_address_high = 0
backplane_prev_address_med  = 0
backplane_prev_address_low  = 0


def set_backplane_address(addr):
    global backplane_prev_address_high, backplane_prev_address_med, backplane_prev_address_low
    # Could do logical and with mask of 0xff_ff_80_00 (same as ~0x7f_ff) but also just do that in the lines below
    addr_high = (addr & 0xff_00_00_00) >> 24
    addr_med  = (addr & 0x00_ff_00_00) >> 16
    addr_low  = (addr & 0x00_00_80_00) >> 8

    
    if ((addr_high != backplane_prev_address_high) or
        (addr_med  != backplane_prev_address_med ) or
        (addr_low  != backplane_prev_address_low )):
        print("++++ Backplane now 0x{0:08X}".format(addr & 0xff_ff_80_00))
    
    
    if addr_high != backplane_prev_address_high:
        cyw_write_reg_u8(BACK_FUNC, BACKPLANE_HIGH_REG, addr_high)
        backplane_prev_address_high = addr_high
    if addr_med != backplane_prev_address_med:
        cyw_write_reg_u8(BACK_FUNC, BACKPLANE_MED_REG, addr_med)
        backplane_prev_address_med = addr_med
    if addr_low != backplane_prev_address_low:
        cyw_write_reg_u8(BACK_FUNC, BACKPLANE_LOW_REG, addr_low)
        backplane_prev_address_low = addr_low

    
# Register read and write for backplane - sets backplane address first

def cyw_read_backplane_bytes(addr, length):
    set_backplane_address(addr)
    addr &= 0x7f_ff
    addr |= SBSDIO_SB_ACCESS_2_4B
    read = cyw_read_bytes(BACK_FUNC, addr, length)
    return read

def cyw_write_backplane_bytes(addr, val, length):
    set_backplane_address(addr)
    addr &= 0x7f_ff
    addr |= SBSDIO_SB_ACCESS_2_4B
    cyw_write_bytes(BACK_FUNC, addr, val, length)

# Register read and write for backplane - sets backplane address first

def cyw_read_backplane_reg_u8(addr):
    read = cyw_read_backplane_bytes(addr, 1)
    return le_bytes_to_u32(read[0:1])

def cyw_read_backplane_reg_u16(addr):
    read = cyw_read_backplane_bytes(addr, 2)
    return le_bytes_to_u32(read[0:2])

def cyw_read_backplane_reg_u32(addr):
    read = cyw_read_backplane_bytes(addr, 4)
    return le_bytes_to_u32(read[0:4])


def cyw_write_backplane_reg_u8(addr, val):
    cyw_write_backplane_bytes(addr, u32_to_le_bytes(val), 1)

def cyw_write_backplane_reg_u16(addr, val):
    cyw_write_backplane_bytes(addr, u32_to_le_bytes(val), 2)
    
def cyw_write_backplane_reg_u32(addr, val):
    cyw_write_backplane_bytes(addr, u32_to_le_bytes(val), 4)

# Controlling the cores

def core_address(core):
    if core == CORE_WLAN:
        core_base = WLAN_ARMCM3_BASE_ADDRESS + WRAPPER_REGISTER_OFFSET
        core_name = "WLAN"
    else:
        core_base = SOCSRAM_BASE_ADDRESS + WRAPPER_REGISTER_OFFSET
        core_name = "SOCSRAM"
    return core_base, core_name

def check_core(core):
    core_base, core_name = core_address(core)
    
    read = cyw_read_backplane_reg_u8(core_base + AI_RESETCTRL_OFFSET)
    if read & AIRC_RESET:
        print("---- Core", core_name, "in reset")
        
def reset_core(core):
    core_base, core_name = core_address(core)
    
    cyw_write_backplane_reg_u8(core_base + AI_IOCTRL_OFFSET, SICF_FGC | SICF_CLOCK_EN)
    cyw_read_backplane_reg_u8(core_base + AI_IOCTRL_OFFSET)
    cyw_write_backplane_reg_u8(core_base + AI_RESETCTRL_OFFSET, 0)
    sleep_ms(1)
    cyw_write_backplane_reg_u8(core_base + AI_IOCTRL_OFFSET, SICF_CLOCK_EN)
    cyw_read_backplane_reg_u8(core_base + AI_IOCTRL_OFFSET)
    sleep_ms(1)

def check_core_up(core):
    core_base, core_name = core_address(core)
    
    #print("---- Checking core", core_name) 
    read = cyw_read_backplane_reg_u8(core_base + AI_IOCTRL_OFFSET)
    if read & (SICF_FGC | SICF_CLOCK_EN) != SICF_CLOCK_EN:
        print("**** Core", core_name, "not up")
    read = cyw_read_backplane_reg_u8(core_base + AI_RESETCTRL_OFFSET)
    if read & AIRC_RESET:
        print("**** Core", core_name, "not up")

# Write firmware
def write_firmware():
    fw = open("fw.bin","rb")
    
    cyw43_fw_len = 231077
    rounded_fw_len = 231080 # rounded to 4 byte boundary
    cyw43_clm_len = 984

    address = 0x00_00_00_00
    
    # WIFI FW rounded to 512 bytes is 231424 (452 x 512)
    # CLM is 984
    # Total file size then 232408

    block_size = 16
    remaining = rounded_fw_len
    chunk_size = 16

    while remaining > 0:
        if remaining < 16:
            chunk_size = remaining
        dat = fw.read(chunk_size)
        cyw_write_backplane_bytes(address, dat, chunk_size)
        #dump_bytes_hex(address, dat)
        address += chunk_size
        remaining -= chunk_size
    #print(hex(address))
    fw.close()

# Write firmware
def write_nvram():
    nvram = open("nvram.bin","rb")
    
    nvram_len = 743
    rounded_nvram_len = 744 # rounded to 4 byte boundary

    top_of_ram_address = 0x00_08_00_00 # 512 * 1204 - top of ram
    magic_address = top_of_ram_address - 4 # place for the magic
    nvram_address = magic_address - rounded_nvram_len
    
    address = nvram_address
    block_size = 16
    remaining = rounded_nvram_len
    chunk_size = 16
    while remaining > 0:
        if remaining < 16:
            chunk_size = remaining
        dat = nvram.read(chunk_size)
        cyw_write_backplane_bytes(address, dat, chunk_size)
        #dump_bytes_hex(address, dat)
        address += chunk_size
        remaining -= chunk_size
    #print(hex(address))
    nvram.close()
    
    # One way to calculate the magic number
    nvram_words = rounded_nvram_len >> 2
    u16_neg_nvram_words = ~nvram_words & 0xffff
    magic = (u16_neg_nvram_words << 16) | nvram_words
        
    #magic  = ((~(rounded_nvram_len >> 2) & 0xffff) << 16) | (rounded_nvram_len >> 2) 
    #print("Magic is ", hex(magic))
    cyw_write_backplane_bytes(magic_address, u32_to_le_bytes(magic), 4)

# Bluetooth firmware - complex file structure
# The file is:
#   1 byte      Number of bytes in version string
#   n bytes     Version string
#   1 byte      Number of records
#       1 byte      Record length
#       2 bytes     Offset address
#       1 byte      Record type
#       n bytes     Record data

ADDR_MODE_UNKNOWN = 0
ADDR_MODE_EXTENDED = 1
ADDR_MODE_SEGMENT = 2
ADDR_MODE_LINEAR32 = 3

TYPE_DATA = 0
TYPE_END_OF_DATA = 1
TYPE_EXTENDED_SEGMENT_ADDRESS = 2
TYPE_EXTENDED_ADDRESS = 4
TYPE_ABSOLUTE_32BIT_ADDRESS = 5

SPI_BUF_SIZE = 64


def write_bt_firmware():
    btfw = open("btfw.bin", "rb")

    data_in = btfw.read(1)
    ver_len = int(data_in[0])
    ver = btfw.read(ver_len)
    print("Bluetooth firmware version: ", end="")
    for c in ver:
        print(chr(c), end="")
    print()

    data_in = btfw.read(1)
    num_recs = int(data_in[0])
    print("Number of records", num_recs)

    addr_low  = 0
    addr_high = 0
    block_len = 0
    buf       = []
    buf_ind   = 0
    my_addr   = 0
    remaining_len = 0

    for i in range(0, num_recs):
        data_in   = btfw.read(4)
        block_len = int(data_in[0]) 
        addr_low  = int(data_in[2]) | (int(data_in[1]) << 8)
        type      = int(data_in[3])
        addr      = addr_high + addr_low
    
        if type == TYPE_EXTENDED_ADDRESS:
            data_in = btfw.read(block_len)
            addr_high =  (int(data_in[0]) << 24) | (int(data_in[1]) << 16)
            addr = addr_high + addr_low
        else:    
            # type 0 or type 1  - type 1 still triggers this final write so it is lucky the files ends with a type 1
            if addr != my_addr + buf_ind:
                if buf_ind != 0:
                    #print("Write address %8x size %4u - final"%(my_addr, buf_ind))  
                    #print_hex("Buffer", buf)

                    cyw_write_backplane_bytes(BTFW_MEM_OFFSET + my_addr, bytes(buf), len(buf))
                    
                    remaining_len = 0
                    buf = []
                    buf_ind = 0
                my_addr = addr
            
            remaining_len += block_len
            to_copy = min(SPI_BUF_SIZE - buf_ind, remaining_len)
            while remaining_len > 0:
                data_in = btfw.read(to_copy)
                buf += data_in
                buf_ind += to_copy
                remaining_len -= to_copy
                if buf_ind == SPI_BUF_SIZE:
                    #print("Write address %8x size %4u"%(my_addr, buf_ind))
                    #print_hex("Buffer", buf)
                    cyw_write_backplane_bytes(BTFW_MEM_OFFSET + my_addr, bytes(buf), len(buf))
                    buf_ind = 0
                    buf = []
                    my_addr += SPI_BUF_SIZE
                to_copy = min(SPI_BUF_SIZE - buf_ind, remaining_len) 
    btfw.close()


# Setup WIFI and BT firmware and configuration

def setup():
    # Send empty bytes to clear 4-bit buffer
    read = spi_transfer(b'x00', 1, 0)  # Just to clear the 4bit extra needed
    
    # Try to read FEEDBEAD
    read = cyw_read_reg_u32_swap(SPI_FUNC, FEEDBEAD_REG)
    print_hex_val_u32("---- SPI transfer read", read)

    # Set configuration
    config = WORD_LENGTH_32 | BIG_ENDIAN | HIGH_SPEED | INT_POLARITY_HIGH | WAKE_UP | INTR_WITH_STATUS
    cyw_write_reg_u32_swap(SPI_FUNC, CONFIG_REG, config) 
    sleep_ms(500)
    
    # Set backplane read padding value
    cyw_write_reg_u8(SPI_FUNC, BACKPLANE_PAD_REG, BACKPLANE_PAD_VALUE)     
    
    # Clear interrupt bits
    config = DATA_UNAVAILABLE | COMMAND_ERROR | DATA_ERROR | F1_OVERFLOW
    cyw_write_reg_u16(SPI_FUNC, SPI_INT_REG, config)
    
    # Enable specific interrupts
    config = F2_F3_FIFO_RD_UNDERFLOW | F2_F3_FIFO_WR_OVERFLOW | COMMAND_ERROR | DATA_ERROR | F2_PACKET_AVAILABLE | F1_OVERFLOW | F1_INTR
    cyw_write_reg_u16(SPI_FUNC, SPI_INT_REG, config)    
    
    # End of setup for SPI functions, now on to backplane resgister functions
    
    # Set ALP clock
    cyw_write_reg_u8(BACK_FUNC, SDIO_CHIP_CLOCK_CSR, SBSDIO_ALP_AVAIL_REQ)
    
    # Set bluetooth watermark
    cyw_write_reg_u8(BACK_FUNC, SDIO_FUNCTION2_WATERMARK, 0x10)
    read = cyw_read_reg_u8(BACK_FUNC, SDIO_FUNCTION2_WATERMARK)
    #print_hex_val_u8("---- Read u8 watermark", read)
    if (read != 0x10):
        print("**** Set bluetooth watermark failed")
        
    # Check ALP available
    read = cyw_read_reg_u8(BACK_FUNC, SDIO_CHIP_CLOCK_CSR)
    #print_hex_val_u8("---- Read chip clock csr", read & SBSDIO_ALP_AVAIL)
    if (read & SBSDIO_ALP_AVAIL == 0):
        print("**** Check ALP available failed")    

    # Clear ALP clock request
    cyw_write_reg_u8(BACK_FUNC, SDIO_CHIP_CLOCK_CSR, 0)
   
    # Check device cores
    check_core(CORE_WLAN)
    check_core(CORE_SOCSRAM)
    
    # Reset SOCSRAM core
    reset_core(CORE_SOCSRAM)    

    # Disable remap for SRAM_3
    cyw_write_backplane_reg_u32(SOCSRAM_BANKX_INDEX, 0x3)
    cyw_write_backplane_reg_u32(SOCSRAM_BANKX_PDA, 0);

    #Read chip number
    read = cyw_read_backplane_reg_u16(CHIPCOMMON_BASE_ADDRESS)
    print("---- Chip id:", read)

    # Write firmware
    write_firmware()

    # Write nvram
    write_nvram()

    sleep_ms(500)    

    # Reset WLAN core
    reset_core(CORE_WLAN)

    # Check cores up
    check_core_up(CORE_WLAN)
    check_core_up(CORE_SOCSRAM) 

    # Check for HT clock
    read = cyw_read_reg_u8(BACK_FUNC, SDIO_CHIP_CLOCK_CSR)
    while (read & SBSDIO_HT_AVAIL) == 0:
        #print_hex_val_u8("---- HT AVAIL", read)
        print(".... Failed HT clock")
        sleep_ms(10000)
        read = cyw_read_reg_u8(BACK_FUNC, SDIO_CHIP_CLOCK_CSR)
    
    # Set interrupt mask
    cyw_write_backplane_reg_u32(SDIO_INT_HOST_MASK, I_HMB_SW_MASK);
    cyw_write_backplane_reg_u32(SDIO_INT_HOST_MASK, I_HMB_FC_CHANGE);

    # Set bluetooth watermark
    cyw_write_reg_u8(BACK_FUNC, SDIO_FUNCTION2_WATERMARK, SPI_F2_WATERMARK)

    # Wait for F2 to be ready
    read = cyw_read_reg_u8(SPI_FUNC, SPI_STATUS_REG)
    while (read & STATUS_F2_RX_READY) == 0:
        #print_hex_val_u8("---- F2 AVAIL", read)
        print(".... Failed F2 ready")
        sleep_ms(1000)
        read = cyw_read_reg_u8(SPI_FUNC, SPI_STATUS_REG)
 
    # Change pad pull up
    cyw_write_reg_u8(BACK_FUNC, SDIO_PULL_UP, 0)
    read = cyw_read_reg_u8(BACK_FUNC, SDIO_PULL_UP)
    
    # Clear data unavailable
    status = cyw_read_reg_u16(SPI_FUNC, SPI_INT_REG)
    if status & DATA_UNAVAILABLE:
        cyw_write_reg_u16(SPI_FUNC, SPI_INT_REG, status)

    # Load bluetooth firmware
    cyw_write_backplane_reg_u32(BTFW_MEM_OFFSET + BT2WLAN_PWRUP_ADDR, BT2WLAN_PWRUP_WAKE);
    write_bt_firmware()
    
    print()

# BT routines

def data_send_toggle():
    val = cyw_read_backplane_reg_u32(HOST_CONTROL_REG)
    val ^= DATA_VALID
    cyw_write_backplane_reg_u32(HOST_CONTROL_REG, val)
 
def host_ready():
    val = cyw_read_backplane_reg_u32(HOST_CONTROL_REG)
    val |= SW_READY
    cyw_write_backplane_reg_u32(HOST_CONTROL_REG, val)
    
def wake_bt():
    val = cyw_read_backplane_reg_u32(HOST_CONTROL_REG)
    new_val = val | WAKE_BT
    if new_val != val:
        cyw_write_backplane_reg_u32(HOST_CONTROL_REG, new_val)

def is_bt_awake():
    return cyw_read_backplane_reg_u32(BT_CONTROL_REG) & BT_AWAKE

def wait_bt_awake():
    while not is_bt_awake():
        print("BT not awake yet")
        sleep_ms(500)
        
def is_bt_ready():
    return cyw_read_backplane_reg_u32(BT_CONTROL_REG) & FW_READY

def wait_bt_ready():
    while not is_bt_ready():
        print("BT not ready yet")    
        sleep_ms(500)
        
def bus_request():
    wake_bt()
    wait_bt_ready()
    

# HCI routines
'''
wifi_base = 0x0 # set this in start-up

def hci_write(dat):
    # need to add prefix of 3 bytes of length and padding at end to make this word aligned
    size = len(dat)
    length_bytes = u32_to_le_bytes(size - 1)[0:3]  # length (excluding the HCI command byte), trimmed to three bytes
    size += 3                                      # add length of the length_bytes
    adjusted_size = (size + 3) & ~3                # round up 
    padding = bytes(adjusted_size - size)          # bytes() of padding
    
    buf = length_bytes + dat + padding             # length prefix + data + padding
    buf_len = len(buf)
    
    send_head = cyw_read_backplane_reg_u32(wifi_base + SEND_HEAD)
    send_tail = cyw_read_backplane_reg_u32(wifi_base + SEND_TAIL)
    
    cyw_write_backplane_bytes(wifi_base + H2BT_BUFFER + send_tail, buf, buf_len)
    cyw_write_backplane_reg_u32(wifi_base + SEND_HEAD, send_tail + buf_len)
    data_send_toggle()

def hci_read():
    receive_head = cyw_read_backplane_reg_u32(wifi_base + RECEIVE_HEAD)
    receive_tail = cyw_read_backplane_reg_u32(wifi_base + RECEIVE_TAIL)

    dat = cyw_read_backplane_bytes(wifi_base + BT2H_BUFFER + receive_tail, receive_head - receive_tail)
    data_send_toggle() 
    cyw_write_backplane_reg_u32(wifi_base + RECEIVE_TAIL, receive_head) # move tail to head, clearing read buffer
    data_send_toggle()
    
    leng = le_bytes_to_u32(dat[0:3])     # get length from first 3 bytes
    return dat[3:3 + leng + 1]           # trim off length 3 byte header and padding bytes trailer

# Main program

power_on()
setup()

wifi_base = cyw_read_backplane_reg_u32(WLAN_BASE_ADDRESS_REG)
print_hex_val_u32("WIFI Base", wifi_base)

# BT ready
host_ready()

# Bus request
bus_request()

print("HCI SEND RECEIVE")
# OCF and OGF reference here: https://software-dl.ti.com/simplelink/esd/simplelink_cc13x2_sdk/1.60.00.29_new/exports/docs/ble5stack/vendor_specific_guide/BLE_Vendor_Specific_HCI_Guide/hci_interface.html
print("SEND x03 x00 x00 x01 x03 x0c x00 x00")
hci_write(b'\x01\x03\x0c\x00') # 0c03 is Reset (3, 1)
dat = hci_read()
print_hex('Received', dat)

print("SEND x03 x00 x00 x01 x01 x10 x00 x00")
hci_write(b'\x01\x01\x10\x00') # 1001 is Read Local Version Information (4, 1)
dat = hci_read()
print_hex('Received', dat)

print("SEND x05 x00 x00 x01 x0c x20 x02 x00 x00")
hci_write(b'\x01\x0c\x20\x02\x00\x00') # 200c is LE Set Scan Enable (8, 2)
dat = hci_read()
print_hex('Received', dat)

print("SEND x03 x00 x00 x01 x03 x0c x00 x00")
hci_write(b'\x01\x03\x0c\x00')
dat = hci_read()
print_hex('Received', dat)

print("SEND x05 x00 x00 x01 x0c x20 x02 x00 x00 x00 x00 x00")
hci_write(b'\x01\x0c\x20\x02\x00\x00')
dat = hci_read()
print_hex('Received', dat)

power_off()
    
'''

class CYW:
    def __init__(self):
        power_on()
        setup()
        self.wifi_base = cyw_read_backplane_reg_u32(WLAN_BASE_ADDRESS_REG)
        print_hex_val_u32("WIFI Base", self.wifi_base)
        host_ready()
        bus_request()
        
    def close(self):
        power_off()

    def send_raw(self, dat):
        # need to add prefix of 3 bytes of length and padding at end to make this word aligned
        size = len(dat)
        length_bytes = u32_to_le_bytes(size - 1)[0:3]  # length (excluding the HCI command byte), trimmed to three bytes
        size += 3                                      # add length of the length_bytes
        adjusted_size = (size + 3) & ~3                # round up 
        padding = bytes(adjusted_size - size)          # bytes() of padding
    
        buf = length_bytes + dat + padding             # length prefix + data + padding
        buf_len = len(buf)
    
        send_head = cyw_read_backplane_reg_u32(self.wifi_base + SEND_HEAD)
        send_tail = cyw_read_backplane_reg_u32(self.wifi_base + SEND_TAIL)
    
        cyw_write_backplane_bytes(self.wifi_base + H2BT_BUFFER + send_tail, buf, buf_len)
        cyw_write_backplane_reg_u32(self.wifi_base + SEND_HEAD, send_tail + buf_len)
        data_send_toggle()

    def receive_raw(self):
        receive_head = cyw_read_backplane_reg_u32(self.wifi_base + RECEIVE_HEAD)
        receive_tail = cyw_read_backplane_reg_u32(self.wifi_base + RECEIVE_TAIL)

        dat = cyw_read_backplane_bytes(self.wifi_base + BT2H_BUFFER + receive_tail, receive_head - receive_tail)
        data_send_toggle() 
        cyw_write_backplane_reg_u32(self.wifi_base + RECEIVE_TAIL, receive_head) # move tail to head, clearing read buffer
        data_send_toggle()
    
        leng = le_bytes_to_u32(dat[0:3])     # get length from first 3 bytes
        return dat[3:3 + leng + 1]           # trim off length 3 byte header and padding bytes trailer

    def readable(self):
        receive_head = cyw_read_backplane_reg_u32(self.wifi_base + RECEIVE_HEAD)
        receive_tail = cyw_read_backplane_reg_u32(self.wifi_base + RECEIVE_TAIL)
        return (receive_head != receive_tail)
      
