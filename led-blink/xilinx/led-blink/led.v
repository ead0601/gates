`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    21:49:31 10/16/2023 
// Design Name: 
// Module Name:    led 
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
`timescale 1ns / 1ps
module led_test
(
        input           clk,           // system clock 50Mhz on board
        input           rst_n,         // reset ,low active
        output reg[3:0] led            // LED,use for control the LED signal on board
);

 //define the time counter
 reg [31:0]      timer;

 // cycle counter:from 0 to 4 sec
 always@(posedge clk or negedge rst_n)
 begin
        if (rst_n == 1'b0)
                timer <= 32'd0;                     //when the reset signal valid,time counter clearing
        else if (timer == 32'd99_999_999)          //4 seconds count(50M*4-1=199999999)
                timer <= 32'd0;                     //count done,clearing the time counter
        else
                timer <= timer + 32'd1;             //timer counter = timer counter + 1
 end

 // LED control
 always@(posedge clk or negedge rst_n)
 begin
        if (rst_n == 1'b0)
                led <= 4'b0000;                     //when the reset signal active
        else if (timer == 32'd24_999_999)       // 49 time counter count to 1st sec,LED1 lighten
                led <= 4'b0001;
        else if (timer == 32'd49_999_999)       // 99 time counter count to 2nd sec,LED2 lighten
                led <= 4'b0010;
        else if (timer == 32'd75_999_999)       // 149 time counter count to 3rd sec,LED3 lighten
                led <= 4'b0100;
        else if (timer == 32'd99_999_999)      // 199 time counter count to 4th sec,LED4 lighten
                led <= 4'b1000;
 end

endmodule

