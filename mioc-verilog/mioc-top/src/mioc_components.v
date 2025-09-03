
   // OUTPUT WIRES
   wire  RA7           ; //: pin 2 : (goes to U9 , RAM Address 7.This is the multiplexed RAM address MSB.)
   wire  BUSRQ_N       ; //: pin18 : Active low bus request
   wire  SPINDIS_N     ; //: pin19 : Active low Controller Spinner Interrupt Disable
   wire  NETRST_N      ; //: pin20 : Active low - Reset for AdamNET
   wire  AUXDECODE1_N  ; //: pin 22 : Active low - Disables the onboard mem decode on CV board?
   wire  RST_N         ; //: pin 23 : Active low reset - System Reset circuitry
   wire  CPRST_N       ; //: pin 24 : Active low reset - not used
   wire  AUXROMCS_N    ; //: pin 26 : Active low aux rom chip select - Slot 2 Expansion ROM CS
   wire  ADDRBUFEN_N   ; //: pin 27 : Active low address buffer enable - according to earlier docs, enables/disables
                         //:     /BRFSH, /BMREQ, /BM1, and /BIORQ (disabled during DMA cycle)
   wire  BOOTROMCS_N   ; //: pin 28 : Active low boot ROM chip select - For Smartwriter ROM
   wire  EN245_N       ; //: pin 29 : Active low 245 enable - CV onboard decode enable/disable?
   wire  IS3_N         ; //: pin 30 : Active low IS3 To Master 6801
   wire  MUX           ; //: pin 37 : Output Mux signal for memory address signals for DRAM.
   wire  RAS_N         ; //: pin 38 : Active low row address strobe
   wire  CAS1_N        ; //: pin 39 : Active low column address strobe 1
   wire  CAS2_N        ; //: pin 40 : Active low column address strobe 2


   // INPUT WIRES - POST IO PAD (pi = post "pad internal")
   //
   // IOPADS have two outputs each: BUF = INV + INV , so either the buffered or inverted signal is used.
   // re-asignment occurs below in the wire assignment section
   //
   wire  PIN_IN_3         ; //: pin 3 : Address line 15
   wire  PIN_IN_4         ; //: pin 4 : Address line 14
   wire  PIN_IN_5         ; //: pin 5 : Address line 13
   wire  PIN_IN_6         ; //: pin 6 : Active low reset signal “Game Reset”
   wire  PIN_IN_7         ; //: pin 7 : Data line 0
   wire  PIN_IN_8         ; //: pin 8 : Data line 1
   wire  PIN_IN_9         ; //: pin 9 : Data line 2
   wire  PIN_IN_10        ; //: pin10 : Data line 3
   wire  PIN_IN_11        ; //: pin11 : Active low write signal Buffered Write (according to earlier docs, gated by MA5,/IORQ, and A10
   wire  PIN_IN_12        ; //: pin12 : Address line 6
   wire  PIN_IN_13        ; //: pin13 : Address line 7 (according to earlier docs, gated by /ADDRBUFEN)
   wire  PIN_IN_13B       ; //: pin13 : INVERTED Address line 7 (according to earlier docs, gated by /ADDRBUFEN)   
   wire  PIN_IN_14        ; //: pin14 : Active low Z80 IO Request
   wire  PIN_IN_15        ; //: pin15 : Active low wait signal, Memory wait state
   wire  PIN_IN_16        ; //: pin16 : Active low bus acknowledge - Z80 Control
   wire  PIN_IN_17        ; //: pin17 : Active low DMA transaction asserted by 6801 to signal DMA to RAM
   wire  PIN_IN_25        ; //: pin 25 : Active low ADAM Reset switch for computer mode
   wire  PIN_IN_31        ; //: pin 31 : Active low OS3 From Master 6801
   wire  PIN_IN_32        ; //: pin 32 : Active low Buffered Memory Request
   wire  PIN_IN_33        ; //: pin 33 : Active low Buffered Memory Read
   wire  PIN_IN_34        ; //: pin 34 : Active low Buffered Memory Refresh
   wire  PIN_IN_35        ; //: pin 35 : Active low Buffered M1, indicates M1 Z80 is in M1 state.
   wire  PIN_IN_36        ; //: pin 36 : Z80 Clock
   
   // INTERNAL COMPONENT WIRES
   //

   // row 1
   wire  w_u1q, w_u1qb;           // u1 output wires 
   wire  w_u2q, w_u2qb;           // u2 output wires 
   wire  w_u3z;
   wire  w_u4z;
   wire  w_u5z;
   wire  w_u6z;
   wire  w_u7z;
   wire  w_u8z;   
   wire  w_u9z;
   wire  w_u10z;
   wire  w_u11z;
   wire  w_u12z;      
   wire  w_u13z;
   wire  w_u14q, w_u14qb;

   // row 2
   wire  w_u17q, w_u17qb;                  
   wire  w_u18z;
   wire  w_u19z;   
   wire  w_u20z;
   wire  w_u21z;
   wire  w_u22z;      
   wire  w_u23z;   
   wire  w_u24z;  
   wire  w_u25z;
   wire  w_u26z;   
   wire  w_u27z;	 
   wire  w_u28z;
   wire  w_u29z;
   wire  w_u30z;
   wire  w_u31z;
   wire  w_u32z;           
   wire  w_u33z;
   wire  w_u34z;                  
   wire  w_u35z;

   // row 3
   wire  w_u37z;   
   wire  w_u38q, w_u38qb;  
   wire  w_u39z;
   wire  w_u40z;
   wire  w_u41z;   
   wire  w_u42z;
   wire  w_u43q, w_u43qb;     
   wire  w_u44z;
   wire  w_u45q, w_u45qb;        
   wire  w_u46z;
   wire  w_u47z;
   wire  w_u48z;
   wire  w_u49z;            
   wire  w_u50z;

   // row 4
   wire  w_u52z;      
   wire  w_u53z;
   wire  w_u54q, w_u54qb;   
   wire  w_u55z;
   wire  w_u56z;   
   wire  w_u57q, w_u57qb;      
   wire  w_u58z;
   wire  w_u59z;
   wire  w_u60q, w_u60qb;         
   wire  w_u61z;
   wire  w_u62z;
   wire  w_u63z;      

   // row 4
   wire  w_u65z;         
   wire  w_u66z;
   wire  w_u67z;
   wire  w_u69z;
   wire  w_u70z;
   wire  w_u71z;         
   wire  w_u72z;         
   wire  w_u73z;         
   wire  w_u74z;         
   wire  w_u75z;         
   wire  w_u76z;            
   wire  w_u77q, w_u77qb;      
   wire  w_u78z;         
   wire  w_u79z;
   wire  w_u80z;
   wire  w_u81z;   
   wire  w_u82z;   
   wire  w_u83z;   
   wire  w_u84z;      

   // row 5
   wire  w_u85z;
   wire  w_u86z;
   wire  w_u87z;
   wire  w_u88q, w_u88qb;         
   wire  w_u89z;
   wire  w_u90q, w_u90qb;            
   wire  w_u91z;
   wire  w_u92q, w_u92qb;            
   wire  w_u93q, w_u93qb;               
   wire  w_u94z;            
   
 
   // COMPONENTS
   //

   // ################################### ROW 1 #############################
   //
   `mioc_flop     u1 (.q(w_u1q),
		      .qbar(w_u1qb),

		      .in1(PIN_IN_25),      // posedge reset	     
		      .in2(w_u39z),         // negedge reset (???)   
		      .in3(PIN_IN_10),      // inverted negedge reset
		      .in4(PIN_IN_6)        // posedge set           
		     );

   `mioc_flop     u2 (.q(w_u2q),      
		      .qbar(w_u2qb),

		      .in1(PIN_IN_25),     // posedge reset	     
		      .in2(w_u39z),        // negedge reset (???)   
		      .in3(PIN_IN_9),	   // inverted negedge reset
		      .in4(PIN_IN_6)	   // posedge set           
	              );

   `mioc_nor2    u3 (.z(w_u3z),
		      .in1(PIN_IN_5),
		      .in2(PIN_IN_4)
		      );

   `mioc_inv1    u4 (.z(w_u4z),
		      .in1(w_u3z)
		      );

   `mioc_nand2    u5 (.z(w_u5z),
		       .in1(w_u4z),
		       .in2(w_u20z)
		       );
   
   `mioc_nor2    u6 (.z(w_u6z),
		      .in1(w_u25z),
		      .in2(w_u18z)
		      );

   `mioc_inv1    u7 (.z(w_u7z),
		      .in1(w_u6z)
		      ); 

   `mioc_nand2    u8 (.z(w_u8z),
		       .in1(w_u24z),
		       .in2(w_u7z)
		       );
   
   `mioc_nand2    u9 (.z(w_u9z),
		       .in1(w_u24z),
		       .in2(w_u10z)
		       );   
   
   `mioc_inv1    u10 (.z(w_u10z),
		      .in1(w_u13z)
		      );
   
   `mioc_inv1    u11 (.z(w_u11z),
		      .in1(PIN_IN_3)
		      );

   `mioc_nor2    u12 (.z(w_u12z),
		      .in1(w_u48z),
		      .in2(w_u11z)
		      );

   `mioc_nor2    u13 (.z(w_u13z),
		      .in1(w_u35z),
		      .in2(w_u48z)
		      );
   
   `mioc_flop     u14 (.q(w_u14q),
		      .qbar(w_u14qb),

		      .in1(1'b0),          // posedge reset	     
		      .in2(PIN_IN_36),     // negedge reset (???)   
		      .in3(w_u49z),        // inverted negedge reset
		      .in4(PIN_IN_34)      // posedge set           
		     );   
      

   // ################################### ROW 2 #############################
   //
   `mioc_flop     u17 (.q(w_u17q),
		       .qbar(w_u17qb),
		       
		       .in1(PIN_IN_25),     // posedge reset	     
		       .in2(w_u39z),        // negedge reset (???)   
		       .in3(PIN_IN_7),      // inverted negedge reset
		       .in4(PIN_IN_6)       // posedge set           
		     );

   `mioc_nor3    u18 (.z(w_u18z),
		      .in1(w_u38qb),
		      .in2(w_u17q),
		      .in3(w_u19z)
		      );

   `mioc_inv1    u19 (.z(w_u19z),
		      .in1(w_u31z)
		      );

   `mioc_nor3    u20 (.z(w_u20z),
		      .in1(w_u38qb),
		      .in2(w_u17qb),
		      .in3(w_u19z)
		      );

   `mioc_inv1    u21 (.z(w_u21z),
		      .in1(w_u26z)
		      );

   `mioc_nand2    u22 (.z(w_u22z),
		       .in1(w_u3z),
		       .in2(w_u20z)
		       );      

   `mioc_xnor2    u23 (.z(w_u23z),
                        .in1(PIN_IN_13),    // ############# PIN 13 ############
                        .in2(w_u44z)
			);

   `mioc_inv1    u24 (.z(w_u24z),
		      .in1(w_u56z)
		      );

   `mioc_nor3    u25 (.z(w_u25z),
		      .in1(w_u1qb),
		      .in2(w_u2q),
		      .in3(w_u28z)
		      );
   
   `mioc_nor3    u26 (.z(w_u26z),
		      .in1(w_u1qb),
		      .in2(w_u2qb),
		      .in3(w_u28z)
		      );

   `mioc_nor3    u27 (.z(w_u27z),
		      .in1(w_u1q),
		      .in2(w_u2qb),
		      .in3(w_u28z)
		      );

   `mioc_inv1    u28 (.z(w_u28z),
		      .in1(w_u12z)
		      );   
   
   `mioc_nand2    u29 (.z(w_u29z),
		       .in1(w_u75z),
		       .in2(w_u60q)
		       );      

   `mioc_nor3    u30 (.z(w_u30z),
		      .in1(w_u1q),
		      .in2(w_u2q),
		      .in3(w_u28z)
		      );

   `mioc_xnor2    u31 (.z(w_u31z),
                        .in1(PIN_IN_3),
                        .in2(w_u48z)
			);   

   `mioc_inv1    u32 (.z(w_u32z),
		      .in1(w_u5z)
		      );   

   `mioc_inv1    u33 (.z(w_u33z),
		      .in1(PIN_IN_36)
		      );

   `mioc_nor3    u34 (.z(w_u34z),
		      .in1(w_u30z),
		      .in2(w_u32z),
		      .in3(w_u41z)
		      );   
   
   `mioc_inv1    u35 (.z(w_u35z),
		      .in1(w_u34z)
		      );
   
   
   // ################################### ROW 3 #############################
   //
   `mioc_nand2    u37 (.z(w_u37z),
		       .in1(PIN_IN_15),
		       .in2(PIN_IN_14)
		       );

   `mioc_flop     u38 (.q(w_u38q),
		       .qbar(w_u38qb),
		       
		       .in1(PIN_IN_25),     // posedge reset	     
		       .in2(w_u39z),        // negedge reset (???)   
		       .in3(PIN_IN_8),      // inverted negedge reset
		       .in4(PIN_IN_6)       // posedge set           
		     );
   
   `mioc_inv1    u39 (.z(w_u39z),
		      .in1(w_u52z)
		      );


   `mioc_inv1    u40 (.z(w_u40z),
		      .in1(w_u55z)
		      );

   `mioc_nor3    u41 (.z(w_u41z),
		      .in1(w_u38q),
		      .in2(w_u17qb),
		      .in3(w_u19z)
		      );
   
   `mioc_nand2    u42 (.z(w_u42z),
		       .in1(w_u21z),
		       .in2(w_u22z)
		       );

   `mioc_flop     u43 (.q(w_u43q),
		       .qbar(w_u43qb),
		       
		       .in1(w_u91z),        // posedge reset	     
		       .in2(w_u57qb),       // negedge reset (???)   
		       .in3(w_u43qb),       // inverted negedge reset
		       .in4(1'b0)           // posedge set           
		     );

   `mioc_nor2    u44 (.z(w_u44z),
		       .in1(w_u60q),
		       .in2(w_u43qb)		       
		      );

   `mioc_flop     u45 (.q(w_u45q),
		       .qbar(w_u45qb),
		       
		       .in1(1'b0),         // posedge reset	     
		       .in2(w_u33z),       // negedge reset (???)   
		       .in3(w_u14q),       // inverted negedge reset
		       .in4(w_u75z)        // posedge set           
		     );

   `mioc_inv1    u46 (.z(w_u46z),
		      .in1(w_u47z)
		      );

   `mioc_nor2    u47 (.z(w_u47z),
		       .in1(w_u54qb),
		       .in2(PIN_IN_36)		       
		      );

   `mioc_inv1    u48 (.z(w_u48z),
		      .in1(w_u78z)
		      );

   `mioc_nand2    u49 (.z(w_u49z),
		       .in1(w_u77q),
		       .in2(w_u29z)
		       );

   `mioc_inv1    u50 (.z(w_u50z),
		      .in1(w_u27z)
		      );

   
   // ################################### ROW 4 #############################
   //
   `mioc_nand2    u52 (.z(w_u52z),
		       .in1(PIN_IN_12),
		       .in2(w_u65z)
		       );
   
   `mioc_nor2    u53 (.z(w_u53z),
		       .in1(PIN_IN_6),
		       .in2(PIN_IN_25)		       
		      );

   
   `mioc_flop     u54 (.q(w_u54q),
		       .qbar(w_u54qb),
		       
		       .in1(1'b0),         // posedge reset	     
		       .in2(w_u46z),       // negedge reset (???)   
		       .in3(w_u37z),       // inverted negedge reset
		       .in4(w_u86z)        // posedge set           
		     );
   
   `mioc_nor3    u55 (.z(w_u55z),
		      .in1(w_u38q),
		      .in2(w_u17q),
		      .in3(w_u19z)
		      );

   `mioc_nand2    u56 (.z(w_u56z),
		       .in1(w_u72z),
		       .in2(w_u73z)
		       );
   
   `mioc_flop     u57 (.q(w_u57q),
		       .qbar(w_u57qb),
		       
		       .in1(w_u91z),        // posedge reset	     
		       .in2(w_u60qb),       // negedge reset (???)   
		       .in3(PIN_IN_12),     // inverted negedge reset
		       .in4(1'b0)           // posedge set           
		     );

   `mioc_nor2    u58 (.z(w_u58z),
		       .in1(w_u75z),
		       .in2(w_u40z)		       
		      );

   `mioc_nor2    u59 (.z(w_u59z),
		       .in1(w_u45q),
		       .in2(w_u14qb)		       
		      );
   
   `mioc_flop     u60 (.q(w_u60q),
		       .qbar(w_u60qb),
		       
		       .in1(1'b0),           // posedge reset	     
		       .in2(PIN_IN_36),       // negedge reset (???)   
		       .in3(w_u62z),         // inverted negedge reset
		       .in4(w_u91z)          // posedge set           
		     );

   `mioc_nor2    u61 (.z(w_u61z),
		       .in1(w_u78z),
		       .in2(w_u77q)		       
		      );   

  `mioc_inv1    u62 (.z(w_u62z),
		      .in1(w_u84z)
		      );

  `mioc_inv1    u63 (.z(w_u63z),
		      .in1(w_u61z)
		      );

   
   // ################################### ROW 5 #############################
   //
   `mioc_nor2    u65 (.z(w_u65z),
		       .in1(PIN_IN_11),
		       .in2(w_u67z)		       
		      );

   `mioc_inv1    u66 (.z(w_u66z),
		      .in1(PIN_IN_12)
		      );   

   `mioc_nand2    u67 (.z(w_u67z),
		       .in1(PIN_IN_13B),   // ############# PIN 13 ############
		       .in2(PIN_IN_14)
		       );

   `mioc_nor2    u69 (.z(w_u69z),
		       .in1(w_u86z),
		       .in2(w_u54q)		       
		      );

   `mioc_nand2    u70 (.z(w_u70z),
		       .in1(w_u67z), 
		       .in2(w_u89z)
		       );

   `mioc_inv1    u71 (.z(w_u71z),
		      .in1(w_u83z)
		      );      
   
   `mioc_nor2    u72 (.z(w_u72z),
		       .in1(PIN_IN_11),
		       .in2(w_u45q)		       
		      );

   `mioc_nor2    u73 (.z(w_u73z),
		       .in1(w_u71z),
		       .in2(w_u45q)		       
		      );

   `mioc_nor2    u74 (.z(w_u74z),
		       .in1(w_u75z),
		       .in2(w_u42z)		       
		      );
   
   `mioc_inv1    u75 (.z(w_u75z),
		      .in1(w_u81z)
		      );      

   `mioc_inv1    u76 (.z(w_u76z),
		      .in1(w_u58z)
		      );      
   

   `mioc_flop     u77 (.q(w_u77q),
		       .qbar(w_u77qb),
		       
		       .in1(1'b0),           // posedge reset	     
		       .in2(w_u33z),         // negedge reset (???)   
		       .in3(w_u45q),         // inverted negedge reset
		       .in4(w_u91z)          // posedge set           
		     );

   `mioc_nor2    u78 (.z(w_u78z),
		       .in1(PIN_IN_16),
		       .in2(w_u69z)		       
		      );

   `mioc_nand2    u79 (.z(w_u79z),
		       .in1(w_u70z),
		       .in2(w_u78z)		       
		      );
   
   `mioc_inv1    u80 (.z(w_u80z),
		      .in1(PIN_IN_36)
		      );      
   
   `mioc_nand4_nor2     u81 (.z(w_u81z),		       
			       .in1(PIN_IN_32),           
			       .in2(w_u78z),         
			       .in3(w_u93q),         
			       .in4(w_u82z)          
			       );

   `mioc_inv1    u82 (.z(w_u82z),
		       .in1(w_u78z)
		       );      

   `mioc_nand4_nor2     u83 (.z(w_u83z),		       
			       .in1(PIN_IN_33),           
			       .in2(w_u78z),         
			       .in3(w_u93q),         
			       .in4(w_u82z)          
			       );

   `mioc_nor2    u84 (.z(w_u84z),
		       .in1(w_u77q),
		       .in2(PIN_IN_35)		       
		      );

   
   // ################################### ROW 6 #############################
   //

   `mioc_inv1    u85 (.z(w_u85z),
		       .in1(w_u87z)
		       );      

   `mioc_inv1    u86 (.z(w_u86z),
		       .in1(PIN_IN_17)
		       );      

   `mioc_nand2    u87 (.z(w_u87z),
		       .in1(w_u66z),
		       .in2(w_u65z)		       
		      );

   `mioc_flop    u88 (.q(w_u88q),      
		      .qbar(w_u88qb),

		      .in1(w_u91z),      // posedge reset	     
		      .in2(w_u85z),      // negedge reset (???)   
		      .in3(PIN_IN_8),	 // inverted negedge reset
		      .in4(1'b0)	 // posedge set           
	              );

   `mioc_inv1    u89 (.z(w_u89z),
		       .in1(w_u70z)
		       );         


   `mioc_flop    u90 (.q(w_u90q),      
		      .qbar(w_u90qb),

		      .in1(w_u91z),      // posedge reset	     
		      .in2(w_u85z),      // negedge reset (???)   
		      .in3(PIN_IN_7),	 // inverted negedge reset
		      .in4(1'b0)	 // posedge set           
	              );

   `mioc_inv1    u91 (.z(w_u91z),
		       .in1(w_u53z)
		       );         

   `mioc_flop    u92 (.q(w_u92q),      
		      .qbar(w_u92qb),

		      .in1(w_u91z),      // posedge reset	     
		      .in2(PIN_IN_31),   // negedge reset (???)   
		      .in3(1'b0),	 // inverted negedge reset
		      .in4(w_u59z)	 // posedge set           
	              );   

   `mioc_flop    u93 (.q(w_u93q),      
		      .qbar(w_u93qb),

		      .in1(w_u91z),      // posedge reset	     
		      .in2(w_u80z),      // negedge reset (???)   
		      .in3(w_u92q),	 // inverted negedge reset
		      .in4(1'b0)	 // posedge set           
	              );

   `mioc_inv1    u94 (.z(w_u94z),
		       .in1(PIN_IN_25)
		       );  
   

