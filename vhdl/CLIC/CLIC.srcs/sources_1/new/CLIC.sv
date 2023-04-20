///////////////////////////////////////////////////////////////////////////////////////////
//                                                                                       //                               
//  Implementation of the Core Local Interrupt Controller (CLIC) for a generic           //
//  RISC-V core.                                                                         //
//                                                                                       //               
///////////////////////////////////////////////////////////////////////////////////////////

module CLIC #(
    parameter NUM_INTERRUPT = 256,
    parameter PRIVILEGED = 0,  // True of false
    parameter PRIORITY_BITS = 7,
    parameter MCLICBASE = 32'b0,  // Section 8.1, base for M mode thinigies
    parameter NVBITS = 0,  // Section 8.2
    // Section 8.4
    parameter CLICANDBASIC = 0,  // Only CLIC mode
    parameter CLICPRIVMODES = 3,  // All privileged modes, likeley pulled to 1 in the future, U/S/M
    parameter CLICLEVELS = 256,
    parameter INTTHRESHBITS = 8
) (
    // Memmory buss adapter
    input clock,
    input reset,
    input write_enable,
    input [31:0] write_data,
    output reg [31:0] read,

    // Peripheral adapter, I think that this is how it should be done
    input  [NUM_INTERRUPT-1:0] per_int_inp,  // Peripheral interrupt input
    output [NUM_INTERRUPT-1:0] per_ack,      // Peripheral interrupt acknowledge
    output [NUM_INTERRUPT-1:0] per_cmplt,    // Peripheral interrupt complete

    // Core interface, core should not need to know the interrupt
    input  [ 1:0] hart_prvlg,      // 0 = machine, 1 = supervisor, 2 = user
    input         hart_ack,
    input         hart_cmplt,
    output        irq,             // Interrupt request
    output [31:0] interrupt_id,    // index in the interrupt vector table
    output [ 1:0] interrupt_level  // 0 = machine, 1 = supervisor, 2 = user
);


  reg [1:0] privilege_level;
  reg [PRIORITY_BITS-1:0] current_priority;



  // Internal access registers 
  reg [31:0] cliccfg[0:0];
  reg [31:0] clicinfo[0:0];
  reg [31:0] clicinttrig[31:0];
  reg [7:0] clicintip[NUM_INTERRUPT-1:0];
  reg [7:0] clicintie[NUM_INTERRUPT-1:0];
  reg [7:0] clicintattr[NUM_INTERRUPT-1:0];
  reg [7:0] clicintctl[NUM_INTERRUPT-1:0];

  wire [ADDRESS_WIDTH-1:0] address_internal = address - ADDRESS;

  // Create the memory map
  REGFILE #(
      .SOURCES(NUM_INTERRUPT)
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
  end



endmodule
