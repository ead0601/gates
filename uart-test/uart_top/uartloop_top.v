//////////////////////////////////////////////////////////////////////
// 
// This testbench will exercise both the UART Tx and Rx in loopback mode
//
`timescale 1ns/10ps
 
`include "/build/repo/gates/uart-test/uart_top/uart_top.v"
 
module uartloop_top(
   input  clk,
   //input  rst,
   input  rx_serial,
		     
   output tx_serial

  );
 
  // Testbench uses a 10 MHz clock
  // Want to interface to 115200 baud UART
  // 10000000 / 115200 = 87 Clocks Per Bit.
  parameter c_CLOCK_PERIOD_NS = 100;
  parameter c_CLKS_PER_BIT    = 87;
  parameter c_BIT_PERIOD      = 8600;
   
  wire       rx_DV;
  wire [7:0] rx_byte;

  // UART_TOP LOOP BACK
  //  
  uart_top #(.c_CLKS_PER_BIT(c_CLKS_PER_BIT)) UART_TOP_INST
    (
      // RX signals
     .i_Clock(clk),
     .i_Rx_Serial(rx_serial),
     .o_Rx_DV(rx_DV),
     .o_Rx_Byte(rx_byte),
   
	  // TX signals
     .i_Tx_DV(rx_DV),
     .i_Tx_Byte(rx_byte),
     .o_Tx_Active(),
     .o_Tx_Serial(tx_serial),
     .o_Tx_Done()
     );
 
   
endmodule

