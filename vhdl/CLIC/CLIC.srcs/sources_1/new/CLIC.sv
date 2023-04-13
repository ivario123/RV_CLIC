///////////////////////////////////////////////////////////////////////////////////////////
//                                                                                       //                               
//  Implementation of the Core Local Interrupt Controller (CLIC) for a generic           //
//  RISC-V core.                                                                         //
//                                                                                       //               
///////////////////////////////////////////////////////////////////////////////////////////

module CLIC #(
    parameter NUMBER_OF_INTERRUPTS = 256,
    parameter PRIVILEGED = 0,  // True of false
    parameter PRIORITY_BITS = 7
) (
    clock,
    reset,
    write_data,
    write_enable,
    read
);
  input clock;
  input reset;
  input write_enable;
  input [31:0] write_data;
  output reg [31:0] read;

  // Internal access registers 
  reg [31:0] cliccfg[0:0];
  reg [31:0] clicinfo[0:0];
  reg [31:0] clicinttrig[31:0];
  reg [31:0] clicintip[NUMBER_OF_INTERRUPTS-1:0];
  reg [31:0] clicintie[NUMBER_OF_INTERRUPTS-1:0];
  reg [31:0] clicintattr[NUMBER_OF_INTERRUPTS-1:0];
  reg [31:0] clicintctl[NUMBER_OF_INTERRUPTS-1:0];


  // Create the memory map
  REGFILE #(
      .SOURCES(NUMBER_OF_INTERRUPTS)
  ) memory (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read),
      .out_cliccfg(cliccfg),
      .out_clicinfo(clicinfo),
      .out_clicinttrig(clicinttrig),
      .out_clicintip(clicintip),
      .out_clicintie(clicintie),
      .out_clicintattr(clicintattr),
      .out_clicintctl(clicintctl)
  );

  // Create the interrupt controller
  always @(posedge clock) begin
    // This will do all of the logic for the CLIC

  end



endmodule
;
