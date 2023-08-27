from amaranth import Elaboratable, Module, Signal
from memory import Memory
from typing import Callable, Dict
from enum import Enum, auto
from helpers.decorators import info, InfoType
from math import log2


class RegisterType(Enum):
    """
    Defines the type of register.
    """

    READ_ONLY = auto()
    WRITE_ONLY = auto()
    READ_WRITE = auto()
    WARL = auto()


class RegisterFile(Elaboratable):
    @info(type=InfoType.MODULE, module="RegisterFile")
    def __init__(
        self,
        start_address=0x0,
        register_width=32,
        register_count=32,
        register_type=RegisterType.READ_WRITE,
        valid: Callable[[int], bool] = lambda _: True,
        initial_values: Callable[[int], int] = lambda _: 0x00000000,
        file_name: str = None,
        file_description: str = None,
        register_descriptors: Dict[str, str] = None,
        bounds_check: bool = True,
    ):
        self.start_address = start_address
        self.register_width = register_width
        self.register_count = register_count
        self.register_type = register_type
        self.valid = valid
        self.file_name = file_name
        self.file_description = file_description
        self.register_descriptors = register_descriptors or {}
        self.bounds_check = bounds_check
        self.is_for_me = Signal()
        self._out_of_bounds = Signal()
        # * inputs
        self.write_enable = Signal()
        self.address = Signal(32)
        self.write_data = Signal(register_width)
        self.reset = Signal()

        # * outputs
        self.read_data = Signal(register_width)

        # * internal
        self.mem = Memory(
            width=register_width,
            depth=register_count,
            reset_value=[initial_values(i) for i in range(register_count)],
        )

    def __str__(self):
        register_descriptors = "\n".join(
            f"\t{k} : {v}" for k, v in self.register_descriptors.items()
        )

        return f"""
        Register file: {self.file_name}
        Register file description: 
        {self.file_description}
        Register count: {self.register_count}
        Register width: {self.register_width}
        Register type: {self.register_type}
        Register descriptors: 
        {'{'}
        {register_descriptors}
        {'}'}
        """

    def __repr__(self):
        return f"<RegisterFile: {self.file_name}@0x{self.address} with {self.register_count} registers>"

    def ports(self):
        return [
            self.write_enable,
            self.address,
            self.write_data,
            self.read_data,
            self.reset,
        ]

    def elaborate(self, platform):
        m = Module()

        m.submodules.read_port = self.read_port = self.mem.read_port()
        m.submodules.write_port = self.write_port = self.mem.write_port()
        read_enable = (
            True
            if self.register_type
            in [RegisterType.READ_ONLY, RegisterType.READ_WRITE, RegisterType.WARL]
            else False
        )
        write_enable = (
            True
            if self.register_type
            in [RegisterType.WRITE_ONLY, RegisterType.READ_WRITE, RegisterType.WARL]
            else False
        )
        # print(f"0x{self.address:x} {self.register_type} {self.register_width}")

        # Create constant for start address
        is_for_me = Signal()
        # Check if the address is for this register file
        m.d.comb += is_for_me.eq(self.address >= self.start_address)
        self.is_for_me = is_for_me
        # Upper bounds check
        is_out_of_bounds = Signal()
        m.d.comb += is_out_of_bounds.eq(
            self.address
            >= self.start_address + self.register_count * int(self.register_width)
        )
        self._out_of_bounds = is_out_of_bounds
        address = Signal.like(self.address)
        # Compute address,
        m.d.comb += address.eq(self.address - self.start_address)
        self._address = address

        # Read data from memory
        if read_enable:
            if self.bounds_check:
                with m.If(is_for_me & ~is_out_of_bounds):
                    m.d.comb += [
                        self.read_port.addr.eq(address),
                        self.read_data.eq(self.read_port.data),
                    ]
                with m.Else():
                    m.d.comb += self.read_data.eq(0x00000000)
            else:
                m.d.comb += [
                    self.read_port.addr.eq(address),
                    self.read_data.eq(self.read_port.data),
                ]
        self.is_for_me = is_for_me
        # Write data to memory
        if write_enable:
            # m.d.comb += self.mem.reset.eq(self.reset)
            # Only write if the address is for this register file
            if self.bounds_check:
                with m.If(is_for_me & ~is_out_of_bounds):
                    write = Signal()
                    if self.register_type == RegisterType.WARL and self.valid:
                        m.d.comb += write.eq(
                            self.write_enable & self.valid(self.write_data)
                        )
                    else:
                        m.d.comb += write.eq(self.write_enable)
                    m.d.sync += [
                        self.write_port.addr.eq(address),
                        self.write_port.data.eq(self.write_data),
                        self.write_port.en.eq(write),
                    ]
            else:
                write = Signal()
                if self.register_type == RegisterType.WARL and self.valid:
                    m.d.comb += write.eq(
                        self.write_enable & self.valid(self.write_data)
                    )
                else:
                    m.d.comb += write.eq(self.write_enable)
                m.d.sync += [
                    self.write_port.addr.eq(address),
                    self.write_port.data.eq(self.write_data),
                    self.write_port.en.eq(write),
                ]

        return m
