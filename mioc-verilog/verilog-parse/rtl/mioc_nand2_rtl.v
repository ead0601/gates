// mioc-nand2
//
// Edward Diaz , 08_21_22
//
// This is a mos representation of the original mos layout
//  configuration that uses an open drain configuration.

// mioc-nand2
//
module mioc_nand2 (
    z,

    in1,            
    in2            
    );

   output z;

   input  in1;
   input  in2;

   assign z = ~(in1 & in2);

endmodule
