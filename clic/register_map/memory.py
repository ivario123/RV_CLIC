from amaranth import Elaboratable, Module, Signal, Array
from typing import List


class Memory:
    """
    A memory class that allows the user to store m n bit value with a specific reset values,
    more or less a coppy of the amaranth example implementation. I just preffer this interface since
    the addressing seems more logical to me.
    """

    def __init__(self, width: int, depth: int, reset_value: List[int] = None) -> None:
        """
        Creates a new memory wrapper. Only for "square" registers
        """
        if reset_value != None and len(reset_value) != depth:
            raise ValueError(
                f"Reset value length ({len(reset_value)}) does not match the depth ({depth})"
            )

        # Number of registers
        self.width = width
        # Depth of each register i.e. number of bits
        self.depth = depth
        # Reset values for signals
        self.reset_values = reset_value
        # List of signals
        self.mem: List[Signal] = Array(
            [
                Signal(width, reset=reset_value[count] if reset_value != None else 0)
                for count in range(self.depth)
            ]
        )

    def read_port(self):
        return ReadPort(self, bus_width=self.width)

    def write_port(self):
        return WritePort(self)


class ReadPort(Elaboratable):
    def __init__(self, memory: Memory, bus_width: int = 32) -> None:
        self.memory = memory

        #! Input signal
        self.addr = Signal(bus_width)

        #! Output signal
        self.data = Signal(bus_width)

    def elaborate(self, platform):
        m = Module()
        # Asynchronous read
        m.d.comb += self.data.eq(self.memory.mem[self.addr])
        return m


class WritePort(Elaboratable):
    def __init__(self, memory: Memory, bus_width: int = 32) -> None:
        self.memory = memory
        #! Input signal
        self.addr = Signal(bus_width)
        self.data = Signal(bus_width)
        self.en = Signal()
        self.reset = Signal()

    def elaborate(self, platform):
        m = Module()
        with m.If(self.reset):
            # Sync reset, this means that we can't reset inbetween clocks but that's fine.
            m.d.sync += self.memory.mem[self.addr].eq(self.memory.mem[self.addr].reset)
        with m.Elif(self.en):
            m.d.sync += self.memory.mem[self.addr].eq(self.data)
        return m
