# Notes on the implementation details for the CLIC module

The Core Local Interrupt Controller (CLIC) is a new interrupt controller for the RISC-V architecture. The CLIC allows for
better real-time performance and lower power consumption than the legacy interrupt controller. The CLIC is designed to be
compatible with the legacy interrupt controller, and can be used as a drop-in replacement for the legacy interrupt controller.

## Notes

### §2.1

$`xtvec`$ 2 bit wide, 00 or 01 yields CLINT mode, 10 or 11 yields CLIC mode.

#### CLINT mode

Supports interrupt preemption based on privilege level not priority.

$`xstatus.xie`$ interrupt enable bit.

- xepc, xcause are interrupt state registers for privilege level x, for M-mode x = m, for S-mode x = s
- xtvec defines the interrupt mode, and points to the interrupt vector table.
- the vector table address is $`xtvec[31:2]`$ and is 4-byte ( or more ) aligned.

## §3

- 4096 interrupts per hart (core or cluster of cores)
- Each interrupts is a block of 4 bytes

```rust
[
    1 byte: clicintip[i] - interrupt pending bit
    1 byte: clicintie[i] - interrupt enable bit
    1 byte: clicintattr[i] - interrupt attributes (priority, level, etc.)
    1 byte: clicintctl[i] - interrupt control
]
```

- Top 16 interrupts can be reserved for CLINT mode interrupts.

### §3.1

- 256 interrupt priority levels ( i.e 8 bit priority )
- Priority 0 is the lowest priority

### §3.2

Existing timer, software and external interrupts are mapped to the top 16 interrupts. These interrupts can be modified as per usual.

## §4

### §4.1 CLIC Memory-Mapped Registers

smclic M-mode CLIC Extension

### §4.1.1 ( Revisit at a later date )

All non existent inputs are tied to 0.

### §4.1.2 Specifying Interrupt Level

0 or 8 level bits ( 0 for CLINT mode, 8 for CLIC mode ) ($`clicintctl[i][4:0]`$)

## §4.2 CLIC Interrupt Pending (clicintip)

interrupt pending should be interpreted as $`(clicintip[i]~\&\&~ clicintie[i]) \neq 0 \rightarrow interrupt~pending`$,
software pending or enabling interrupts must take effect in a bounded amount of time ( I would like to have this bound to 1 cycle ). However there is no hard requirement that the $`clicintie`$ or $`clicintip`$ be evaluated immediately after explicit write to them.
