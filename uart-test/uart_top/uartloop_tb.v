////////////////////////////////////////////////////////////////////////
// 
// This testbench will exercise both the UART Tx and Rx in loopback mode
//
`timescale 1ns/10ps
 
`include "/build/repo/gates/uart-test/uart_top/uartloop_top.v"
 
module uartloop_tb();

  // Testbench uses a 10 MHz clock
  // Want to interface to 115200 baud UART
  // 10000000 / 115200 = 87 Clocks Per Bit.
  parameter c_CLOCK_PERIOD_NS = 100;
  parameter c_CLKS_PER_BIT    = 87;
  parameter c_BIT_PERIOD      = 8600;
   
  reg        clk;
  reg        rx_serial;
  wire       tx_serial;
   
  // Takes in input byte and serializes it 
  task UART_WRITE_BYTE;
    input [7:0] i_Data;
    integer     ii;
    begin
       
      // Send Start Bit
      rx_serial <= 1'b0;
      #(c_BIT_PERIOD);
      #1000;
       
      // Send Data Byte
      for (ii=0; ii<8; ii=ii+1)
        begin
          rx_serial <= i_Data[ii];
          #(c_BIT_PERIOD);
        end
       
      // Send Stop Bit
      rx_serial <= 1'b1;
      #(c_BIT_PERIOD);
     end
  endtask // UART_WRITE_BYTE
   

  task UART_READ_BYTE;
    reg [7:0] i_Data;
    integer     ii;
    begin
       
      // Send Start Bit
      @ (negedge tx_serial);      // <= 1'b0;
      #(c_BIT_PERIOD);
      #1000;
       
      // Send Data Byte
      for (ii=0; ii<8; ii=ii+1)
        begin
          i_Data[ii] <= tx_serial;
          #(c_BIT_PERIOD);
        end
       
      // Send Stop Bit
       @ (posedge tx_serial);     // <= 1'b1;
      #(c_BIT_PERIOD);
     end
  endtask // UART_READ_BYTE


   
  // DUT : UART_TOP LOOP BACK
  //  
  uartloop_top #(.c_CLKS_PER_BIT(c_CLKS_PER_BIT)) UARTLOOP_TOP_INST
    (
      // RX signals
     .clk(clk),
     .rx_serial(rx_serial),
     
     .tx_serial(tx_serial)
     );
   

  always
    #(c_CLOCK_PERIOD_NS/2) clk <= !clk;

   
  // Main Testing:
  initial
    begin
	   rx_serial <= 1'b1;
	   clk       <= 1'b0;
		
		#(c_BIT_PERIOD);
       
      // Tell UART to send a command (exercise Tx)
      @(posedge clk);
      @(posedge clk);
       
      // Send a command to the UART (exercise Rx)
      @(posedge clk);
      UART_WRITE_BYTE(8'h3F);
      @(posedge clk);
      UART_READ_BYTE();
      @(posedge clk);
             
      // Check that the correct command was received
      //if (w_Rx_Byte == 8'h3F)
      //  $display("Test Passed - Correct Byte Received");
      //else
      //  $display("Test Failed - Incorrect Byte Received");
       
    end
 
endmodule

