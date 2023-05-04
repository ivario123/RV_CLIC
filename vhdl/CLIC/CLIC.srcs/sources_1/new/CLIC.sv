///////////////////////////////////////////////////////////////////////////////////////////
//                                                                                       //                               
//  Implementation of the Core Local Interrupt Controller (CLIC) for a generic           //
//  RISC-V core.                                                                         //
//                                                                                       //               
///////////////////////////////////////////////////////////////////////////////////////////



/*
Functionality outline:

1. Usecase: Interrupts from peripherals
  1. A peripheral raises an interrupt request -> per_int_inp[any] == 1
  2. The CLIC checks if the interrupt is enabled -> clicintie[any] == 1
  3. The CLIC checks if the interrupt is pending -> clicintip[any] == 1
  4. The CLIC checks if the interrupt is higher priority than the current interrupt -> clicintctl[any] > current_priority
  5. The CLIC sets the interrupt request -> irq = 1 if all of the above are true
  6. The CLIC sets the interrupt id -> interrupt_id = i
  7. The CLIC sets the interrupt level -> interrupt_level = privilege_level
  8. The core acknowledges the interrupt -> hart_ack = 1
  9. The CLIC clears the interrupt request -> irq = 0
  Time passes
  10. The core completes the interrupt -> hart_cmplt = 1
  11. The CLIC sets the interrupt complete -> per_cmplt[i] = 1
  12. The CLIC clears the interrupt complete -> per_cmplt[i] = 0
2. Usecase: Specify interrupt priority
  1. The core writes to the interrupt priority via the memory map

  


*/

typedef enum logic [1:0] {
  POS_LEVEL,
  POS_EDGE,
  NEG_LEVEL,
  NEG_EDGE
} trigger_t;


module CLIC #(
    parameter NUM_INTERRUPT = 256,
    parameter PRIVILEGED = 0,  // True of false
    parameter PRIORITY_BITS = 8,
    parameter MCLICBASE = 32'b0,  // Section 8.1, base for M mode thinigies
    parameter NVBITS = 0,  // Section 8.2
    // Section 8.4
    parameter CLICANDBASIC = 0,  // Only CLIC mode
    parameter CLICPRIVMODES = 3,  // All privileged modes, likeley pulled to 1 in the future, U/S/M
    parameter CLICLEVELS = 256,
    parameter INTTHRESHBITS = 8,

    // Derived parameters
    parameter INTERRUPT_ID_BITS = $clog2(NUM_INTERRUPT)
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

    // Core interface
    input      [ 1:0] hart_prvlg,      // 0 = machine, 1 = supervisor, 2 = user
    input             hart_ack,
    input             hart_cmplt,
    output reg        irq,             // Interrupt request
    output reg [31:0] interrupt_id,    // index in the interrupt vector table
    output reg [ 1:0] interrupt_level  // 0 = machine, 1 = supervisor, 2 = user
);


  reg [1:0] privilege_level;
  reg [PRIORITY_BITS-1:0] current_priority;
  initial begin
    privilege_level  = 0;
    current_priority = 0;
  end



  // Internal access registers 
  reg [31:0] cliccfg[0:0];
  reg [31:0] clicinfo[0:0];
  reg [31:0] clicinttrig[31:0];
  reg [7:0] clicintip[NUM_INTERRUPT-1:0];
  reg [7:0] clicintie[NUM_INTERRUPT-1:0];
  reg [7:0] clicintattr[NUM_INTERRUPT-1:0];
  reg [7:0] clicintctl[NUM_INTERRUPT-1:0];

  // wire [31:0] address_internal = address - ADDRESS;

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
  // These are optional but will be implemented at a later date
  typedef struct packed {
    logic enabeld;  // Bit 31 of clicinttrig
    logic [12:0] base;  // Bits 12:0 of clicinttrig
  } debug_trigger_t;  // Optional but nice for debugging, triggers
  debug_trigger_t debug_triggers[31:0];

  /* 
    Create a packed struct interrupt for each interrupt
  */
  typedef struct packed {
    // logic [1:0] privilege_level; //  This would be needed if we were using more than M mode, now it is pulled to 0b11, since we are not using 
    // the privilege level we don't need to use it when comparing the priorities
    trigger_t trigger;  // Found in clicintattr[2:1]
    // Priority is left adjusted and extended with interruptid
    logic [PRIORITY_BITS+INTERRUPT_ID_BITS-1:0] prio;  // Found in clicintctl[PRIORITY_BITS:0], these are left justified
    logic pending;  // Found in clicintip[0]
    logic enabled;  // Found in clicintie[0]
  } interrupt_t;
  interrupt_t interrupts[NUM_INTERRUPT-1:0];
  interrupt_t highest_priority_interrupt;

  // Connect the abstracted interrupt to the internal registers
  always_comb begin
    for (int i = 0; i < NUM_INTERRUPT; i++) begin
      // Typecast the trigger
      trigger_t inter_mediate_trigger = trigger_t'(clicintattr[i][2:1]);
      logic [INTERRUPT_ID_BITS-1:0] id = i[INTERRUPT_ID_BITS-1:0];
      interrupts[i].prio = {clicintctl[i][PRIORITY_BITS-1:0], id};
      interrupts[i].trigger = inter_mediate_trigger;
      interrupts[i].pending = clicintip[i][0];
      interrupts[i].enabled = clicintie[i][0];
    end
    for (int i = 0; i < 31; i++) begin
      debug_triggers[i].enabeld = clicinttrig[i][31];
      debug_triggers[i].base = clicinttrig[i][12:0];
    end
  end
  // On per_int_inp[any] == 1, set the pending bit of the interrupt



  /*
    Create 2 different always blocks, one for each trigger type
  */

  // level sensitive
  always_comb begin
    for (int i = 0; i < NUM_INTERRUPT; i++) begin
      if (interrupts[i].enabled && interrupts[i].pending != 1) begin
        // Check if the interrupt is enabled and not already pending

        // Check that the interrupt trigger condition is met
        if (interrupts[i].trigger == POS_LEVEL && per_int_inp[i] == 1) begin
          interrupts[i].pending = per_int_inp[i];
        end
      end
    end
  end


  // edge sensitive for edge per_int_inp[i] == 1
  // not sure if this is the correct way to do it
  always @(posedge per_int_inp) begin
    for (int i = 0; i < NUM_INTERRUPT; i++) begin
      if (interrupts[i].enabled && interrupts[i].pending != 1) begin
        // Check if the interrupt is enabled and not already pending
        // Check that the interrupt trigger condition is met
        if (interrupts[i].trigger == POS_EDGE && per_int_inp[i] == 1) begin
          interrupts[i].pending = per_int_inp[i];
        end
      end
    end
  end

  // edge sensitive for edge per_int_inp[i] == 0
  // not sure if this is the correct way to do it

  always @(negedge per_int_inp) begin
    for (int i = 0; i < NUM_INTERRUPT; i++) begin
      if (interrupts[i].enabled && interrupts[i].pending != 1) begin
        // Check if the interrupt is enabled and not already pending
        // Check that the interrupt trigger condition is met
        if (interrupts[i].trigger == NEG_EDGE && per_int_inp[i] == 0) begin
          interrupts[i].pending = per_int_inp[i];
        end
      end
    end
  end



  always_comb begin
    for (int i = 0; i < NUM_INTERRUPT; i++) begin
      if (per_ack[i] == 1) begin
        interrupts[i].pending = 0;
      end
    end
  end
  always_comb begin
    interrupt_id[INTERRUPT_ID_BITS-1:0] = highest_priority_interrupt.prio[INTERRUPT_ID_BITS-1:0];  //  Only the INTERRUPT_ID_BITS LSB are used
    interrupt_level = 2'b11;  // Always machine mode
  end
  
  always @(posedge hart_ack && negedge clock) begin
    // Clock after hart_ack is negedge
    
    irq = 0;  // Reset the irq since core has acknowledged it  
  end

  always @(posedge clock) begin
    highest_priority_interrupt = 0;  // Reset the highest_priority_interrupt
    // Find first enabeld interrupt with pending bit set
    for (int i = 0; i < NUM_INTERRUPT; i++) begin
      if (interrupts[i].enabled && interrupts[i].pending) begin
        // Check that a highest_priority_interrupt has been set
        // if not set it to the current interrupt
        if (highest_priority_interrupt.prio == 0 && interrupts[i].prio[PRIORITY_BITS+6:7] > current_priority) begin
          highest_priority_interrupt = interrupts[i];
        end else if (highest_priority_interrupt.prio < interrupts[i].prio) begin
          highest_priority_interrupt = interrupts[i];
        end
      end
    end
    // If a highest_priority_interrupt has been set, set the irq
    if (highest_priority_interrupt != 0) begin
      irq = 1;
    end else begin
        // if no interrupt is pending we are not in an interrupt
        irq = 0;

        current_priority = 0;
    end
  end







  // Create the interrupt controller
  always @(posedge clock) begin

  end



endmodule
