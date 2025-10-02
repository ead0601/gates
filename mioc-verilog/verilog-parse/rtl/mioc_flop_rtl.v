// mioc-flop-mos
//
// Edward Diaz , 08_21_22
//
// This is a RTL representation of the original mos layout
// configuration that uses an open drain configuration. This
// was created because of an issuesimulating the NMOS version 
// with ICARUS verilog
//

`timescale 1ns / 1 ns

// mioc-flop-rtl
//
module mioc_flop (
    q,
    qbar,

    ar,        // async   reset
    nclk,      // negedge clk         // negedge reset (???)
    din,       // sync    D          // inverted negedge reset  
    as         // async   set
    );

   output q;
   output qbar;

   input  ar;    // in1;
   input  nclk;  // in2;
   input  din;   // in3;
   input  as;    // in4;

   reg    qr, n_qr; 

   always @(negedge nclk, posedge ar, posedge as) begin
      if (ar == 1'b1)
	qr <= 1'b0;
      else if (as == 1'b1) begin
	qr <= 1'b1;
      end
      else begin
	 qr <= n_qr;
      end      
   end
   
   always @(din) begin
      n_qr = in3;
   end
   
   assign q = qr;
   assign qbar = ~qr;
    
endmodule
