`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    23:54:44 10/17/2023 
// Design Name: 
// Module Name:    uart_top 
// Project Name: 
// Target Devices: 
// Tool versions: 
// Description: 
//
// Dependencies: 
//
// Revision: 
// Revision 0.01 - File Created
// Additional Comments: 
//
//////////////////////////////////////////////////////////////////////////////////

`include "/build/repo/gates/uart-test/uart_top/uart_tx.v"
`include "/build/repo/gates/uart-test/uart_top/uart_rx.v"

module uart_top 
   #(parameter c_CLKS_PER_BIT = 87)
   (

    // RX signals
    input        i_Clock,
    input        i_Rx_Serial,
    output       o_Rx_DV,
    output [7:0] o_Rx_Byte,
	
	 // TX signals
    input       i_Tx_DV,
    input [7:0] i_Tx_Byte, 
    output      o_Tx_Active,
    output      o_Tx_Serial,
    output      o_Tx_Done
   );
	 	 
  uart_rx #(.CLKS_PER_BIT(c_CLKS_PER_BIT)) UART_RX_INST
    (.i_Clock(i_Clock),
     .i_Rx_Serial(i_Rx_Serial),
     .o_Rx_DV(),
     .o_Rx_Byte(o_Rx_Byte)
     );
   
  uart_tx #(.CLKS_PER_BIT(c_CLKS_PER_BIT)) UART_TX_INST
    (.i_Clock(i_Clock),
     .i_Tx_DV(i_Tx_DV),
     .i_Tx_Byte(i_Tx_Byte),
     .o_Tx_Active(),
     .o_Tx_Serial(),
     .o_Tx_Done(o_Tx_Done)
     );

endmodule
