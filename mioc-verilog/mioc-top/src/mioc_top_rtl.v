// mioc-top
//
// Edward Diaz , 08_21_22
//
// This is a mos representation of the original mos layout
//  configuration that uses an open drain configuration.

// mioc-top
//

// Abstract devices
//
`define mioc_nor3        mioc_nor3_rtl           
`define mioc_flop        mioc_flop_rtl       
`define mioc_xnor2       mioc_xnor2_rtl      
`define mioc_nand4_nor2  mioc_nand4_nor2_rtl 
`define mioc_nand2       mioc_nand2_rtl      
`define mioc_inv1        mioc_inv1_rtl       
`define mioc_nor2        mioc_nor2_rtl       
 
// Instantiate top
//
module mioc_top(
                                 //: pin 1 : VCC  
		
		RA7          ,   //: pin 2 : (goes to U9 , RAM Address 7.This is the multiplexed RAM address MSB.)	    
		BA15         ,	 //: pin 3 : Address line 15								    
		BA14         ,	 //: pin 4 : Address line 14								    
		BA13         ,	 //: pin 5 : Address line 13								    
				                                                                                            
		N_CVRST      ,	 //: pin 6 : Active low reset signal “Game Reset”					    
		BD0          ,	 //: pin 7 : Data line 0								    
		BD1          ,	 //: pin 8 : Data line 1								    
		BD2          ,	 //: pin 9 : Data line 2								    
		BD3          ,	 //: pin10 : Data line 3								    
		N_BWR        ,	 //: pin11 : Active low write signal Buffered Write (according to earlier docs, gated by    
				 //:      by MA5,/IORQ, and A10								    
		BA6          ,	 //: pin12 : Address line 6								    
		BA7          ,	 //: pin13 : Address line 7 (according to earlier docs, gated by /ADDRBUFEN)		    
		IORQ_N       ,	 //: pin14 : Active low Z80 IO Request							    
		WAIT_N       ,	 //: pin15 : Active low wait signal, Memory wait state					    
		BUSAK_N      ,	 //: pin16 : Active low bus acknowledge - Z80 Control					    
		DMA_N        ,	 //: pin17 : Active low DMA transaction asserted by 6801 to signal DMA to RAM		    
		BUSRQ_N      ,	 //: pin18 : Active low bus request							    
		SPINDIS_N    ,	 //: pin19 : Active low Controller Spinner Interrupt Disable				    
		NETRST_N     ,	 //: pin20 : Active low - Reset for AdamNET                                                 

                                 //: pin 21 : GND
		
		AUXDECODE1_N ,   //: pin 22 : Active low - Disables the onboard mem decode on CV board?				 
		RST_N        ,	 //: pin 23 : Active low reset - System Reset circuitry						 
		CPRST_N      ,	 //: pin 24 : Active low reset - not used							 
		PBRST_N      ,	 //: pin 25 : Active low ADAM Reset switch for computer mode					 
		AUXROMCS_N   ,	 //: pin 26 : Active low aux rom chip select - Slot 2 Expansion ROM CS				 
		ADDRBUFEN_N  ,	 //: pin 27 : Active low address buffer enable - according to earlier docs, enables/disables	 
				 //:     /BRFSH, /BMREQ, /BM1, and /BIORQ (disabled during DMA cycle)				 
		BOOTROMCS_N  ,	 //: pin 28 : Active low boot ROM chip select - For Smartwriter ROM				 
		EN245_N      ,	 //: pin 29 : Active low 245 enable - CV onboard decode enable/disable?				 
		IS3_N        ,	 //: pin 30 : Active low IS3 To Master 6801							 
		OS3_N        ,	 //: pin 31 : Active low OS3 From Master 6801							 
		BMREQ_N      ,	 //: pin 32 : Active low Buffered Memory Request						 
		BRD_N        ,	 //: pin 33 : Active low Buffered Memory Read							 
		BRFSH_N      ,	 //: pin 34 : Active low Buffered Memory Refresh						 
		BM1_N        ,	 //: pin 35 : Active low Buffered M1, indicates M1 Z80 is in M1 state.				 
		B_PHI        ,	 //: pin 36 : Z80 Clock										 
		MUX          ,	 //: pin 37 : Output Mux signal for memory address signals for DRAM.				 
		RAS_N        ,	 //: pin 38 : Active low row address strobe							 
		CAS1_N       ,	 //: pin 39 : Active low column address strobe 1						 
		CAS2_N       	 //: pin 40 : Active low column address strobe 2                                                 
		);
   
                         //: pin 1 : VCC  

   output RA7          ; //: pin 2 : (goes to U9 , RAM Address 7.This is the multiplexed RAM address MSB.)	    
   input  BA15         ; //: pin 3 : Address line 15								    
   input  BA14         ; //: pin 4 : Address line 14								    
   input  BA13         ; //: pin 5 : Address line 13								    
	                                                                                                            
   input  N_CVRST      ; //: pin 6 : Active low reset signal “Game Reset”					    
   input  BD0          ; //: pin 7 : Data line 0								    
   input  BD1          ; //: pin 8 : Data line 1								    
   input  BD2          ; //: pin 9 : Data line 2								    
   input  BD3          ; //: pin10 : Data line 3								    
   input  N_BWR        ; //: pin11 : Active low write signal Buffered Write (according to earlier docs, gated by    
                         //:      by MA5,/IORQ, and A10								    
   input  BA6          ; //: pin12 : Address line 6								    
   input  BA7          ; //: pin13 : Address line 7 (according to earlier docs, gated by /ADDRBUFEN)		    
   input  IORQ_N       ; //: pin14 : Active low Z80 IO Request							    
   input  WAIT_N       ; //: pin15 : Active low wait signal, Memory wait state					    
   input  BUSAK_N      ; //: pin16 : Active low bus acknowledge - Z80 Control					    
   input  DMA_N        ; //: pin17 : Active low DMA transaction asserted by 6801 to signal DMA to RAM		    
   output BUSRQ_N      ; //: pin18 : Active low bus request							    
   output SPINDIS_N    ; //: pin19 : Active low Controller Spinner Interrupt Disable				    
   output NETRST_N     ; //: pin20 : Active low - Reset for AdamNET                                                  

                         //: pin 21 : GND

   output AUXDECODE1_N ; //: pin 22 : Active low - Disables the onboard mem decode on CV board?				 
   output RST_N        ; //: pin 23 : Active low reset - System Reset circuitry						 
   output CPRST_N      ; //: pin 24 : Active low reset - not used							 
   input  PBRST_N      ; //: pin 25 : Active low ADAM Reset switch for computer mode					 
   output AUXROMCS_N   ; //: pin 26 : Active low aux rom chip select - Slot 2 Expansion ROM CS				 
   output ADDRBUFEN_N  ; //: pin 27 : Active low address buffer enable - according to earlier docs, enables/disables	 
                         //:     /BRFSH, /BMREQ, /BM1, and /BIORQ (disabled during DMA cycle)				 
   output BOOTROMCS_N  ; //: pin 28 : Active low boot ROM chip select - For Smartwriter ROM				 
   output EN245_N      ; //: pin 29 : Active low 245 enable - CV onboard decode enable/disable?				 
   output IS3_N        ; //: pin 30 : Active low IS3 To Master 6801							 
   input  OS3_N        ; //: pin 31 : Active low OS3 From Master 6801							 
   input  BMREQ_N      ; //: pin 32 : Active low Buffered Memory Request						 
   input  BRD_N        ; //: pin 33 : Active low Buffered Memory Read							 
   input  BRFSH_N      ; //: pin 34 : Active low Buffered Memory Refresh						 
   input  BM1_N        ; //: pin 35 : Active low Buffered M1, indicates M1 Z80 is in M1 state.				 
   input  B_PHI        ; //: pin 36 : Z80 Clock										 
   output MUX          ; //: pin 37 : Output Mux signal for memory address signals for DRAM.				 
   output RAS_N        ; //: pin 38 : Active low row address strobe							 
   output CAS1_N       ; //: pin 39 : Active low column address strobe 1						 
   output CAS2_N       ; //: pin 40 : Active low column address strobe 2                                                 


   // COMPONENTS
   `include "./src/mioc_components.v"   
   
   // WIRE ASSIGNMENTS
   //
   `include "./src/mioc_pin_assignments.v"
   
endmodule
