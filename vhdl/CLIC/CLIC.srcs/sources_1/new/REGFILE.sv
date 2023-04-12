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
    output [31:0] out_clicintip[SOURCES-1:0],
    output [31:0] out_clicintie[SOURCES-1:0],
    output [31:0] out_clicintattr[SOURCES-1:0],
    output [31:0] out_clicintctl[SOURCES-1:0]

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

  REGBLOCK #(
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(32),
      .START_ADDRESS(32'h0040)
  ) clicinttrig (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicinttrig)
  );

  REGBLOCK #(
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1000),
      .REG_SPACING(4 * 4)
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
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1001),
      .REG_SPACING(4 * 4)
  ) clicintie (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicintie)
  );

  REGBLOCK #(
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1002),
      .REG_SPACING(4 * 4)
  ) clicintattr (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicintattr)
  );

  REGBLOCK #(
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1003),
      .REG_SPACING(4 * 4)
  ) clicintctl (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read_data),
      .registers(out_clicintctl)
  );
endmodule
;
