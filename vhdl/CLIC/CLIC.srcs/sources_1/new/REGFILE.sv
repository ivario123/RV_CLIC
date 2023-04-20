///////////////////////////////////////////////////////////////////////////////////////////////
// Defines the register map for the RISC-V CLIC (Core Local Interrupt Controller)            //
// See                                                                                       //
//                                                                                           //
// github.com/riscv/riscv-fast-interrupt/blob/master/clic.adoc                               //
//                                                                                           //
// for more information.                                                                     //
///////////////////////////////////////////////////////////////////////////////////////////////

/*

Memory Map
  Offset

### 0x0008-0x003F              reserved ###

### 0x00C0-0x07FF              reserved ###

### 0x0800-0x0FFF              custom ###

  0x0000         1B          RW        cliccfg
  0x0004         4B          R         clicinfo

  0x0040         4B          RW        clicinttrig[0]
  0x0044         4B          RW        clicinttrig[1]
  0x0048         4B          RW        clicinttrig[2]
  ...
  0x00B4         4B          RW        clicinttrig[29]
  0x00B8         4B          RW        clicinttrig[30]
  0x00BC         4B          RW        clicinttrig[31]

  0x1000+4*i     1B/input    R or RW   clicintip[i]
  0x1001+4*i     1B/input    RW        clicintie[i]
  0x1002+4*i     1B/input    RW        clicintattr[i]
  0x1003+4*i     1B/input    RW        clicintctl[i]
  ...
  0x4FFC         1B/input    R or RW   clicintip[4095]
  0x4FFD         1B/input    RW        clicintie[4095]
  0x4FFE         1B/input    RW        clicintattr[4095]
  0x4FFF         1B/input    RW        clicintctl[4095]

*/

// Note: This is the first thing I write in SystemVerilog, so it's probably not the best code.
// I'm also not sure if this is the best way to do this, but it works.

// We need to expose internal registers to the super module, so we need to use the "reg" keyword.



module REGFILE #(
    parameter SOURCES = 256
) (
    input clock,
    input reset,
    input [31:0] address,
    input write_enable,
    input [31:0] write_data,
    output reg [31:0] read_data,
    output [31:0] out_cliccfg[0:0],
    output [31:0] out_clicinfo[0:0],
    output [31:0] out_clicinttrig[31:0],
    output [7:0] out_clicintip[SOURCES-1:0],
    output [7:0] out_clicintie[SOURCES-1:0],
    output [7:0] out_clicintattr[SOURCES-1:0],
    output [7:0] out_clicintctl[SOURCES-1:0]

);
  /*
    There are a few cases:
    1. Address is in the range of 0x0000-0x0004 (cliccfg and clicinfo)
    2. Address is in the range of 0x0040-0x00BC (clicinttrig) ( subtract 0x0040 and divide by 4 to get the index )
    3. Address is in the range of 0x1000-0x4FFF (clicintip, clicintie, clicintattr, clicintctl) ( subtract 0x1000 and divide by 4 to get the index )
    4. Address is in the range of 0x0008-0x003F, 0x00C0-0x07FF, 0x0800-0x0FFF (reserved)
    5. Address is in the range of 0x0005-0x003F, 0x00BD-0x07FF, 0x1000-0x4FFF (reserved)
    */

  REGBLOCK #(
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(1),
      .START_ADDRESS(32'h0000)
  ) cliccfg (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_cliccfg)
  );

  REGBLOCK #(
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(1),
      .START_ADDRESS(32'h004)
  ) clicinfo (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicinfo)
  );

  // Need to use distinct module for WARL registers since they have 
  // specific behaviour for specific write_data values.
  clicinttrig #(
      .SOURCES(32)
  ) clicinttrig_reg (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data_in(write_data),
      .read_data(read_data),
      .registers(out_clicinttrig)
  );

  REGBLOCK #(
      .DATA_WIDTH(8),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1000),
      .REG_SPACING(4) // This equates to 4 registers inbetween each register, which means that we wrap around to the next register.
  ) clicintip (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicintip)
  );

  REGBLOCK #(
      .DATA_WIDTH(8),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1001),
      .REG_SPACING(4)
  ) clicintie (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicintie)
  );

  // Specifies behaviour for clicintattr register.
  // This is a WARL register, so we need to specify the behaviour for specific write_data values.
  clicintattr #(
      .SOURCES(SOURCES)
  ) clicintattr_reg (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data_in(write_data),
      .read_data(read_data),
      .registers(out_clicintattr)
  );


  // While this is a WARL register we will set it WARA (Write Any Value, Read Any Value)
  // since we want to use all 4096 interrupts.
  REGBLOCK #(
      .DATA_WIDTH(8),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1003),
      .REG_SPACING(4) // This equates to 4 registers inbetween each register, which means that we wrap around to the next register.
  ) clicintctl (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicintctl)
  );

  // ===========================================================
  //                        CSRREGISTERS
  // ===========================================================

  REGISTER #(
      .ADDRESS(32'h300)
  ) mstatus (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data)
  );
  // Trap-handler base address / interrupt mode
  REGISTER #(
      .ADDRESS(32'h305),
      .WIDTH  (8)
  ) mtvec (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Trap-handler vector table base address
  REGISTER #(
      .ADDRESS(32'h307),
      .WIDTH(32)  // Not sure about this one, only logical imo since address width is 32
  ) mtvt (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data)
  );
  // Scratch register for trap handlers
  REGISTER #(
      .ADDRESS(32'h340),
      .WIDTH  (8)
  ) mscratch (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Exception program counter
  REGISTER #(
      .ADDRESS(32'h341),
      .WIDTH  (8)
  ) mepc (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Cause of trap
  REGISTER #(
      .ADDRESS(32'h342),
      .WIDTH  (8)
  ) mcause (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Bad address or instruction
  REGISTER #(
      .ADDRESS(32'h343),
      .WIDTH  (8)
  ) mtval (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Interrupt handler address and enable modifier
  REGISTER #(
      .ADDRESS(32'h345),
      .WIDTH(16)  // Really not sure about this one, think it's one per interrupt??
  ) mnxti (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[15:0]),
      .read_data(read_data[15:0])
  );
  // Interrupt-level threshold
  REGISTER #(
      .ADDRESS(32'h347),
      .WIDTH  (8)
  ) mintthresh (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Conditional scratch swap on priv mode change
  REGISTER #(
      .ADDRESS(32'h348),
      .WIDTH  (8)
  ) mscratchcsw (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Conditional scratch swap on level change
  REGISTER #(
      .ADDRESS(32'h349),
      .WIDTH  (8)
  ) mscratchcswl (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
  // Current interrupt levels
  REGISTER #(
      .ADDRESS(32'hFB1),
      .WIDTH(8)  // Really not sure about this one, think it's one per interrupt??
  ) mintstatus (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data[7:0]),
      .read_data(read_data[7:0])
  );
endmodule


module REGISTER #(
    parameter WIDTH = 32,
    parameter ADDRESS_WIDTH = 32,
    parameter DEFAULT_VALUE = 0,
    parameter ADDRESS = 0
) (
    input [WIDTH-1:0] write_data,
    input [ADDRESS_WIDTH-1:0] address,
    input write_enable,
    input clock,
    input reset,

    output reg [WIDTH-1:0] read_data
);
  initial begin
    read_data <= DEFAULT_VALUE;
  end
  always @(posedge clock) begin
    unique case (reset) inside
      1: read_data <= DEFAULT_VALUE;
      0: begin

        unique case (address) inside
          ADDRESS: begin
            unique case (write_enable) inside
              0: read_data <= read_data;
              1: read_data <= write_data;
            endcase
          end
          default: begin
            read_data <= 0;
          end
        endcase
      end
    endcase
  end
endmodule
