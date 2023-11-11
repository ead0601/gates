"""
This python program was created to model a Verilog implmentation of an SDIO controller.
It will be used to debug SDR and DDR burst read/write transactions, by using a FT232H
module to SDIO 4bit module. Once all transactions are verified, the implmentation will
be converted to Verilog.

-Edward Diaz

CRC7 generator: https://rndtool.info/CRC-step-by-step-calculator/

Generator polynomial: G(x) = x7 + x3 + 1
CRC poly: 10001001

CRC7 Examples
The CRC section of the command/response is bolded.
CMD0 (Argument=0) --> 01 000000 00000000000000000000000000000000 "1001010" 1
CMD17 (Argument=0) --> 01 010001 00000000000000000000000000000000 "0101010" 1
Response of CMD17 --> 00 010001 00000000000000000000100100000000 "0110011" 1

"""

from pyftdi.ftdi import Ftdi
from pyftdi.gpio import GpioBaseController
from pyftdi.gpio import GpioMpsseController
from pyftdi.gpio import GpioAsyncController
from pyftdi.gpio import GpioSyncController
from time import sleep
import struct

# List all devices
#
Ftdi.show_devices()

PIN_0 =0x001
PIN_1 =0x002
PIN_2 =0x004
PIN_3 =0x008
PIN_4 =0x010
PIN_5 =0x020

PIN_6 =0x000
PIN_7 =0x000
#PIN_6 =0x040
#PIN_7 =0x080

PIN_IDX    = { "CMD_PIN" : 0, "CLK_PIN" : 1, "D0_PIN" : 2, "D1_PIN" : 3, "D2_PIN" : 4, "D3_PIN" : 5 } 
PIN_LIST   = [ (0,"CMD_PIN"), (1,"CLK_PIN"), (2,"D0_PIN"), (3,"D1_PIN"), (4,"D2_PIN"), (5,"D3_PIN") ]
PIN_STATE  = [ 1 , 1 , 1 , 1 , 1 , 1 ]

def setup_ftdi_device():

    #gpio = GpioAsyncController()
    gpio = GpioSyncController()

    # Open the FT232H (you might need to adjust the URL)
    url = 'ftdi://ftdi:232h/1'
    gpio.configure(url, direction=0x0FF) # ALL OUTPUTS
    #gpio.set_frequency(1000000)     #  1MHz
    #gpio.set_frequency(10000000)   # 10MHz
    gpio.set_frequency(16000)      # 16Khz
    return gpio
                

# ###################################################################################################

class parameters:
    # convert to verilog parameter statements
    #
    START_INIT          =  0  # 5'd00;  // Send initialization clock pulses to the deselected SD card.    
    SEND_CMD0           =  1  # 5'd01;  // Put the SD card in the IDLE state.
    CHK_CMD0_RESPONSE   =  2  # 5'd02;  // Check card's R1 response to the CMD0.
    SEND_CMD8           =  3  # 5'd03;  // This command is needed to initialize SDHC cards.
    GET_CMD8_RESPONSE   =  4  # 5'd04;  // Get the R7 response to CMD8.
    SEND_CMD55          =  5  # 5'd05;  // Send CMD55 to the SD card. 
    SEND_CMD41          =  6  # 5'd06;  // Send CMD41 to the SD card.
    CHK_ACMD41_RESPONSE =  7  # 5'd07;  // Check if the SD card has left the IDLE state.     
    WAIT_FOR_HOST_RW    =  8  # 5'd08;  // Wait for the host to issue a read or write command.
    RD_BLK              =  9  # 5'd09;  // Read a block of data from the SD card.
    WR_BLK              = 10  # 5'd10;  // Write a block of data to the SD card.
    WR_WAIT             = 11  # 5'd11;  // Wait for SD card to finish writing the data block.
    START_TX            = 12  # 5'd12;  // Start sending command/data.
    TX_BITS             = 13  # 5'd13;  // Shift out remaining command/data bits.
    GET_CMD_RESPONSE    = 14  # 5'd14;  // Get the R1 response of the SD card to a command.
    RX_BITS             = 15  # 5'd15;  // Receive response/data from the SD card.
    DESELECT            = 16  # 5'd16;  // De-select the SD card and send some clock pulses (Must enter with sclk at zero.)
    PULSE_SCLK          = 17  # 5'd17;  // Issue some clock pulses. (Must enter with sclk at zero.)
    REPORT_ERROR        = 18  # 5'd18;  // Report error and stall until reset.
    
    CMD0_C              = 0x40 + 0 
    CMD8_C              = 0x40 + 8 
    CMD55_C             = 0x40 + 55 
    CMD41_C             = 0x40 + 41 
    READ_BLK_CMD_C      = 0x40 + 17 
    WRITE_BLK_CMD_C     = 0x40 + 24 
    
    FAKE_CRC_C          = "11111111" 

class registers:    
    # convert to verilog reg definitions
    cstate              = 0
    n_cstate            = 0
    rstate              = 0
    n_rstate            = 0
    pindir              = "110000"     # // 6'h7F, pin direction, 1=>output
    n_pindir            = "110000"     # // 6'h7F, pin direction, 1=>output
    bitcnt              = 0 
    n_bitcnt            = 0 
    toutcnt             = 0 
    n_toutcnt           = 0 
    clk                 = 0 
    n_clk               = 0 
    cmd_o               = 1            
    n_cmd_o             = 1 
    d0_o                = 0            
    n_d0_o              = 0 
    d1_o                = 0            
    n_d1_o              = 0            
    d2_o                = 0            
    n_d2_o              = 0            
    d3_o                = 0            
    n_d3_o              = 0 
    cmd_i               = 1 
    n_cmd_i             = 1            
    d0_i                = 0 
    n_d0_i              = 0            
    d1_i                = 0            
    n_d1_i              = 0            
    d2_i                = 0            
    n_d2_i              = 0            
    d3_i                = 0            
    n_d3_i              = 0            
    cmd_reg             = 0 
    n_cmd_reg           = 0 
    get_resp            = 0 
    n_get_resp          = 0  
    flush_fifo          = 0
    edge_count          = 0
    cmd_resp            = ""
    
# Init value fifo
class fifos:
    outfifo = []
    infifo  = []
    
    
# ###################################################################################################    

def extract_response(data):
    resp = ""
    for d in data:
        if (d[-2] == '1'):
            resp = resp + d[-1]
    firstzero = resp.find("0")
    resp = resp[(firstzero):(firstzero+48)]
    return(resp)


# Push next value into the FIFO
#
def push_next_value_fifo(gpio, reg, fifo, depth):

    # The FT232H has an internal FIFO, and we are using the GPIO API of PYFTDI.
    # the async mode is not used because control of reads is unpredictable.
    # In sync mode both writes and reads occur in unison with the exchange function.
    # The verilog model had to modified to account for this burst transaction method.
    
    # Assemble infividual states into byte value. (incl. clk and cmd)
    #
    value = 0x00
    index =  PIN_IDX["D0_PIN"];  value = value | (PIN_STATE[ index ] << index)
    index =  PIN_IDX["D1_PIN"];  value = value | (PIN_STATE[ index ] << index)
    index =  PIN_IDX["D2_PIN"];  value = value | (PIN_STATE[ index ] << index)
    index =  PIN_IDX["D3_PIN"];  value = value | (PIN_STATE[ index ] << index)
    index =  PIN_IDX["CLK_PIN"]; value = value | (PIN_STATE[ index ] << index)
    index =  PIN_IDX["CMD_PIN"]; value = value | (PIN_STATE[ index ] << index)

    # Next pin value to be pushed int the FIFO (bit 0 is numerical)
    value = value & 0xFF

    # Direction values are store as a string so pindir[0] is located to the left
    # instead of the right, and needs to be flipped.
    flip = reg.pindir[::-1]
    dir = int(flip,2) & 0xFF

    # Push into FIFO, and flush FIFO out when full
    # (when called with flush, no NEW value will be pushed in)
    #
    if (reg.flush_fifo == 1):
        # Forced flush event
        gpio.set_direction(0x3F,dir)

        # Send Writes
        pinread = gpio.exchange(bytearray(fifo.outfifo))

        # Process reads
        intlist = list(pinread)
        reads = [bin(x) for x in intlist]
        resp  = extract_response(reads)
        reg.cmd_resp = resp

        # Clear FIFO no value appended
        fifo.outfifo = []
        #fifo.outfifo.append(value)
        reg.flush_fifo = 0
        
    elif (len(fifo.outfifo) < depth):     # depth was 1024
        # Push new value into the FIFO
        fifo.outfifo.append(value)
        
    else:
        # Buffer overflow occurred, force flush and insert new value
        gpio.set_direction(0x3F,dir)

        # Send writes
        pinread = gpio.exchange(bytearray(fifo.outfifo))

        # Process reads
        intlist = list(pinread)
        reads = [bin(x) for x in intlist]
        resp  = extract_response(reads)
        reg.cmd_resp = resp

        # Clear FIFO, and append new value
        fifo.outfifo = []
        fifo.outfifo.append(value)
        

# always @ posedge
#
def sync_process(gpio, par, reg, fifo):

    pin_cmd = PIN_IDX["CMD_PIN"]
    pin_clk = PIN_IDX["CLK_PIN"]
    pin_d0  = PIN_IDX["D0_PIN"]
    pin_d1  = PIN_IDX["D1_PIN"]
    pin_d2  = PIN_IDX["D2_PIN"]
    pin_d3  = PIN_IDX["D3_PIN"]
    
    # Global count used to drive events
    #
    if (reg.edge_count < 1):
        reg.edge_count = reg.edge_count + 1
    else:
        reg.edge_count = 0

    # SYNC process, where all registers are instantiated.
    #
    # Drive CLK PIN  / \ / \
    #                0 1 0 1

    # Assign next posedge states, create next state logic on negedge of clk   
    if (reg.edge_count == 1):
        # NEGEDGE: edge_count == 1
        par, reg, fifo = assign_next_state(gpio, par, reg, fifo)
        reg.clk = reg.n_clk
               
    else:
        # POSEDGE: edge_count == 0
        reg.clk = 1
        
    # always @ posedge
    if (reg.edge_count == 0):
        reg.cstate       = reg.n_cstate   # // current state
        reg.rstate       = reg.n_rstate   # // return state
        reg.pindir       = reg.n_pindir   # // current pins direction
        reg.cmd_o        = reg.n_cmd_o    # // next command pin value
        reg.d0_o         = reg.n_d0_o     # // next d0 pin value
        reg.d1_o         = reg.n_d1_o     # // next d1 pin value
        reg.d2_o         = reg.n_d2_o     # // next d2 pin value
        reg.d3_o         = reg.n_d3_o     # // next d3 pin value            
        reg.cmd_i        = reg.n_cmd_i    # // next command pin value
        reg.d0_i         = reg.n_d0_i     # // next d0 pin value
        reg.d1_i         = reg.n_d1_i     # // next d1 pin value
        reg.d2_i         = reg.n_d2_i     # // next d2 pin value
        reg.d3_i         = reg.n_d3_i     # // next d3 pin value            
        reg.bitcnt       = reg.n_bitcnt
        reg.toutcnt      = reg.n_toutcnt
        reg.cmd_reg      = reg.n_cmd_reg 
        reg.get_resp     = reg.n_get_resp  

        # Assign statements
        #
        PIN_STATE[pin_clk] = int(reg.clk)      # // next clk pin

        if (reg.pindir[pin_cmd] == "1"):             # // 1=>outputs
          PIN_STATE[pin_cmd] = int(reg.cmd_o)  # // next command pin value
          reg.n_cmd_i = 1               
        else:
          reg.n_cmd_i = PIN_STATE[pin_cmd] 
          #print("reg.n_cmd_i:",reg.n_cmd_i)
          #print("reg.cmd_i:",reg.cmd_i)
          
        if (reg.pindir[pin_d0] == "1"):    # // 1=>outputs
          PIN_STATE[pin_d0] = int(reg.d0_o)       # // next d0 pin value
          PIN_STATE[pin_d1] = int(reg.d1_o)       # // next d1 pin value
          PIN_STATE[pin_d2] = int(reg.d2_o)       # // next d2 pin value
          PIN_STATE[pin_d3] = int(reg.d3_o)       # // next d3 pin value            
          reg.n_d0_i  = 0               # // next d0 pin value
          reg.n_d1_i  = 0               # // next d1 pin value
          reg.n_d2_i  = 0               # // next d2 pin value
          reg.n_d3_i  = 0               # // next d3 pin value            
        else:
          reg.n_d0_i  = PIN_STATE[pin_d0]     # // next d0 pin value
          reg.n_d1_i  = PIN_STATE[pin_d1]     # // next d1 pin value
          reg.n_d2_i  = PIN_STATE[pin_d2]     # // next d2 pin value
          reg.n_d3_i  = PIN_STATE[pin_d3]     # // next d3 pin value            

    # always @ negedge    
    elif (reg.edge_count == 1):
        reg.clk = reg.n_clk             
        
        # Assign statements
        PIN_STATE[pin_clk] = int(reg.clk)        
    
    
# On the negedge of clock assign all of the next state values,
# so that on the posedge event, all of the registered value transfers(D->Q) occur.
#
def assign_next_state(gpio, par, reg, fifo):

    """
    Assign all the values for the next clock state
 
    This function only get called, quater cycle pre posedgeclk, 

    """

    reg.n_clk      = reg.clk          
    reg.n_cmd_o    = reg.cmd_o   
    reg.n_d0_o     = reg.d0_o       
    reg.n_d1_o     = reg.d1_o       
    reg.n_d2_o     = reg.d2_o       
    reg.n_d3_o     = reg.d3_o       
    reg.n_cstate   = reg.cstate 
    reg.n_rstate   = reg.rstate 
    reg.n_pindir   = reg.pindir 
    reg.n_bitcnt   = reg.bitcnt 
    reg.n_toutcnt  = reg.toutcnt
    reg.n_cmd_reg  = reg.cmd_reg
    reg.n_get_resp = reg.get_resp  

    # Used IF/ELSE and needs to be converted to a CASE since python-3.8 does not have a case statement
    #
    if (reg.cstate == par.START_INIT):
        reg.n_clk    = 0;
        reg.n_pindir = "110000"
        reg.n_cmd_o  = 1
        reg.n_cstate = par.PULSE_SCLK
        reg.n_rstate = par.SEND_CMD8
        reg.n_bitcnt = 80
        key = input("Press any key to continue.")


    elif (reg.cstate == par.PULSE_SCLK):
        reg.n_clk         = not reg.clk            # // Toggle clock line

        if (reg.bitcnt == 0):
            reg.n_clk = 0
            reg.n_cmd_o = 1
            reg.n_cstate = reg.rstate
            
            reg.flush_fifo = 1                      # // Force fifo to be flushed
            push_next_value_fifo(gpio, reg, fifo, 1024)
            reg.flush_fifo = 0                      # // Force fifo to be flushed

        else:
            reg.n_cstate = par.PULSE_SCLK
            reg.n_bitcnt = reg.bitcnt - 1

    elif (reg.cstate == par.SEND_CMD8):
        print("SEND_CMD8")
        sleep(0.020)
        reg.n_clk      = 0
        reg.n_cmd_o    = 1 
        reg.n_cstate   = par.START_TX 
        #reg.n_rstate   = par.GET_CMD8_RESPONSE
        reg.n_rstate   = par.SEND_CMD41
        reg.n_pindir   = "110000"   # 0x30, 1=>output
        reg.n_bitcnt   = 49
        reg.n_cmd_reg  = "0" + bin(par.CMD8_C)[2:] + "0000"*5 + "000110101010" + "10000111" + "11" # // 0x87 is correct CRC
        reg.n_get_resp = 1
    
    elif (reg.cstate == par.SEND_CMD41):
        print("SEND_CMD41")
        sleep(0.020)
        reg.n_clk      = 0
        reg.n_cmd_o    = 1 
        reg.n_cstate   = par.START_TX 
        reg.n_rstate   = par.CHK_ACMD41_RESPONSE 
        reg.n_pindir   = "110000"   # 0x30, 1=>output
        reg.n_bitcnt   = 49       
        #reg.n_cmd_reg  = "0" + bin(par.CMD41_C)[2:] + "0100" + "0000"*7 + par.FAKE_CRC_C + "11"
        reg.n_cmd_reg  = "0" + bin(par.CMD41_C)[2:] + "0100" + "0000"*7 + "0111011" + "111"	
        reg.n_get_resp = 1
        
    elif (reg.cstate == par.START_TX):
        # // Start sending command/data by lowering SCLK and outputing MSB of command/data
        # // so it has plenty of setup before the rising edge of SCLK.
        reg.n_clk         = 0                      # // Lower the SCLK (although it should already be low).
        reg.n_cmd_o       = reg.cmd_reg[0] 
        reg.n_cmd_reg     = reg.cmd_reg[1:]        # // Shift MSBs out
        reg.n_bitcnt      = reg.bitcnt - 1         
        reg.n_cstate      = par.TX_BITS            # // Go here to shift out the rest of the command/data bits.

    elif (reg.cstate == par.TX_BITS):              # // Shift out remaining command/data bits and get response from SD card.
        reg.n_clk         = 0                      # // Toggle clock line

        if (reg.bitcnt != 0):                      # // Keep sending bits until the bit counter hits zero.
            reg.n_cmd_o       = reg.cmd_reg[0] 
            reg.n_cmd_reg     = reg.cmd_reg[1:]    # // Shift MSBs out
            reg.n_bitcnt      = reg.bitcnt - 1         
        else:
            if (reg.get_resp == 1):
                reg.n_cmd_o  = 1                   # // Clear output CMD bit so that start bit can signal the start
                reg.n_cstate = par.GET_CMD_RESPONSE    # // Get a response to the command from the SD card.
                
                # !!!!!!!!!!!!!!!!!!!!!!  TEMP WORK AROUND DUE TO PYFTDI SYNC FIFO READ METHOD !!!!!!!!!!!!!  
                reg.n_bitcnt = 60  # 48            # // Length of the expected response.
                reg.n_toutcnt = 1 #  64            # // Set thetimeout counter

                reg.n_pindir = "010000"            # // 0x10, 1=>output, cmd become input

                reg.flush_fifo = 1                      # // Force fifo to be flushed
                push_next_value_fifo(gpio, reg, fifo, 1024)
                reg.flush_fifo = 0                 # // Force fifo to be flushed

                print("command:  ",reg.cmd_resp)
                
            else:
                reg.n_cstate = reg.rstate          # // Return to calling state (no need to get a response).
                
    elif (reg.cstate == par.GET_CMD_RESPONSE):     # // Get the response of the SD card to a command.
        reg.n_clk       = 0                        # // Toggle clock line
        reg.flush_fifo  = 0

        if (reg.cmd_i == 0):                       # wait for response start bit going low
              reg.n_cmd_reg =  "0" * 48 + str(reg.cmd_i)
              reg.n_bitcnt  = reg.bitcnt - 1 
              reg.n_cstate  = par.RX_BITS          # // Now receive the reset of the response.
              #reg.n_toutcnt = 500                  # got a response, no longer need to check timeout
        else:
            reg.n_toutcnt  = reg.toutcnt - 1 
            if (reg.toutcnt == 0):
              # !!!!!!!!!!!!!!!!!!!!!!  TEMP WORK AROUND DUE TO PYFTDI SYNC FIFO READ METHOD !!!!!!!!!!!!!  
              reg.n_cstate  = par.RX_BITS          # // Now receive the reset of the response.                
              #reg.n_cstate = par.START_INIT 
              #print("GET_CMD_RESPONSE: timeout counter expired, no response.")
            else:
              reg.n_cstate = par.GET_CMD_RESPONSE

    elif (reg.cstate == par.RX_BITS):               # // Receive bits from the SD card.
        reg.n_clk       = 0                         # // Toggle clock line
        reg.flush_fifo  = 0
        
        #reg.n_cmd_reg = reg.cmd_reg[46:0] + str(reg.cmd_i)
        if (reg.bitcnt != 0):
            reg.n_bitcnt  = reg.bitcnt - 1 
            reg.n_cstate  = par.RX_BITS             # // Now receive the reset of the response.
        else:
            reg.n_pindir   = "010000"               # // Keep CMD as input until TX, 1=>output, cmd become input            
            reg.n_cstate   = reg.rstate             # // Otherwise, return to calling state without de-selecting.
            reg.get_resp   = 0
            
            reg.flush_fifo = 1                      # // Force fifo to be flushed
            push_next_value_fifo(gpio, reg, fifo, 1024)
            reg.flush_fifo = 0                      # // Force fifo to be flushed
            
            print("response: ",reg.cmd_resp)
            
    elif (reg.cstate == par.CHK_ACMD41_RESPONSE):
        # // The CMD55, CMD41 sequence should cause the SD card to leave the IDLE state
        # // and become ready for SPI read/write operations. If still IDLE, then repeat the CMD55, CMD41 sequence.
        # // If one of the R1 error flags is set, then report the error and stall.

        #print("CHK_ACMD41_RESPONSE: " + reg.cmd_reg)
        reg.n_clk = 0                               # // Lower the SCLK (although it should already be low).  
        reg.n_cstate = par.START_INIT
        reg.n_pindir = "010000"                     # // Keep CMD as input until TX, 1=>output, cmd become input 
            
    else:
        print("Warning!! Default case: reached")
        reg.n_clk = 0                               # // Lower the SCLK (although it should already be low).  
        reg.n_cstate = par.START_INIT
        reg.n_pindir = "010000"                     # // Keep CMD as input until TX, 1=>output, cmd become input 
        
    return(par,reg,fifo)

# ###################################################################################################

# Main function
#
def main():
    gpio = setup_ftdi_device()

    reg  = registers()
    par  = parameters()
    fifo = fifos()

    # Global counter used for timing reference
    edge_count      = 0

    # Initial process : CMD_PIN & CLK_PIN
    #
    reg.flush_fifo = 0

    reg.cstate     = par.START_INIT   # // 5'h00, current stat
    reg.n_cstate   = par.START_INIT   # // 5'h00, next current state
    reg.rstate     = par.START_INIT   # // 5'h00, return state 
    reg.n_rstate   = par.START_INIT   # // 5'h00, next return state   
    reg.pindir     = "110000"         # // 6'h7F, pin direction, 1=>output
    reg.n_pindir   = "110000"         # // 6'h7F, pin direction, 1=>output
    
    reg.cmd_o   = 1 
    reg.n_cmd_o = 1 
    reg.cmd_i   = 1 
    reg.n_cmd_i = 1 
    reg.n_d0_i  = 0               # // next d0 pin value
    reg.n_d1_i  = 0               # // next d1 pin value
    reg.n_d2_i  = 0               # // next d2 pin value
    reg.n_d3_i  = 0               # // next d3 pin value            
    reg.clk     = 0 
    reg.n_clk   = 0     

    # Main process loop
    #
    while(1):
        # Display current state
        # print(edge_count,reg.cstate,reg.n_cstate)

        # Sync process
        sync_process(gpio, par, reg, fifo)
        
        # Update pins
        push_next_value_fifo(gpio, reg, fifo, 1024)         
                      

if __name__ == '__main__':
    main()

