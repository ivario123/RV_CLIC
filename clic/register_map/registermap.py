from amaranth import Cat
from .registerfile import *
from . import *

"""


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


"""


class RegisterMap(Elaboratable):
    class BaseAddresses(Enum):
        CLICCFG = 0x0000
        CLICINFO = 0x0004
        CLICINTTRIG = 0x0040
        CLICINTIP = 0x1000
        CLICINTIE = 0x1001
        CLICINTATTR = 0x1002
        CLICINTCTL = 0x1003

    write_able_addresses = [
        BaseAddresses.CLICCFG,
        BaseAddresses.CLICINTTRIG,
        BaseAddresses.CLICINTIE,
        BaseAddresses.CLICINTATTR,
        BaseAddresses.CLICINTCTL,
        BaseAddresses.CLICINTIP,
    ]

    # @info(type=InfoType.MODULE, module="RegisterMap")
    def __init__(
        self,
    ):
        self.address = Signal(32)
        self.write_data = Signal(32)
        self.write_enable = Signal()
        self.reset = Signal()
        self.read_data = Signal(32)
        self.is_quad_mapped = Signal()
        """
        Creates the memory map for the CLIC
        """
        # * cliccfg
        self.cliccfg = RegisterFile(
            register_count=1,
            register_width=8,
            register_type=RegisterType.READ_WRITE,
            initial_values=lambda _: 0x00,
            file_name="cliccfg",
            file_description="CLIC configuration register",
            start_address=self.BaseAddresses.CLICCFG.value,
        )
        # * clicinfo
        self.clicinfo = RegisterFile(
            register_count=1,
            register_width=32,
            register_type=RegisterType.READ_ONLY,
            initial_values=lambda _: 0x00,
            file_name="clicinfo",
            file_description="CLIC information register",
            start_address=self.BaseAddresses.CLICINFO.value,
        )
        # * clicinttrig
        self.clicinttrig = RegisterFile(
            register_count=32,
            register_width=32,
            register_type=RegisterType.READ_WRITE,
            initial_values=lambda _: 0x00,
            file_name="clicinttrig",
            file_description="CLIC interrupt trigger register",
            start_address=self.BaseAddresses.CLICINTTRIG.value,
        )
        self.clicintip = RegisterFile(
            register_count=4096,
            register_width=8,
            register_type=RegisterType.READ_WRITE,
            initial_values=lambda _: 0x00,
            file_name="clicintip",
            file_description="CLIC interrupt pending register",
            start_address=0x0,  # Has to be remapped in this module
            bounds_check=True,  # No need to check bounds, as that is handled by this module
        )

        # * clicintie
        self.clicintie = RegisterFile(
            register_count=4096,
            register_width=8,
            register_type=RegisterType.READ_WRITE,
            initial_values=lambda _: 0x00,
            file_name="clicintie",
            file_description="CLIC interrupt enable register",
            start_address=0x0,  # Has to be remapped in this module
            bounds_check=True,  # No need to check bounds, as that is handled by this module
        )

        # * clicintattr
        self.clicintattr = RegisterFile(
            register_count=4096,
            register_width=8,
            register_type=RegisterType.READ_WRITE,
            initial_values=lambda _: 0x00,
            file_name="clicintattr",
            file_description="CLIC interrupt attribute register",
            start_address=0x0,  # Has to be remapped in this module
            bounds_check=True,  # No need to check bounds, as that is handled by this module
        )

        # * clicintctl
        self.clicintctl = RegisterFile(
            register_count=4096,
            register_width=8,
            register_type=RegisterType.READ_WRITE,
            initial_values=lambda _: 0x00,
            file_name="clicintctl",
            file_description="CLIC interrupt control register",
            start_address=0x0,  # Has to be remapped in this module
            bounds_check=True,  # No need to check bounds, as that is handled by this module
        )
        self.regs = [
            self.cliccfg,
            self.clicinfo,
            self.clicinttrig,
            self.clicintip,
            self.clicintie,
            self.clicintattr,
            self.clicintctl,
        ]

    def ports(self):
        return [
            self.address,
            self.write_data,
            self.write_enable,
            self.read_data,
        ]

    def elaborate(self, platform):
        m = Module()

        # Change mapping if we are above certain threshold
        m.d.comb += self.is_quad_mapped.eq(self.address >= 0x1000)

        def add_module(self, m, *modules):
            # Add submodules
            local_dict = {"m": m, "self": self}
            for module in modules:
                exec(f"m.submodules.{module} = self.{module}", local_dict, globals())
            # This is fine since the function only exists in this scope.
            locals().update(local_dict)
            return self, m

        self, m = add_module(
            self,
            m,
            "cliccfg",
            "clicinfo",
            "clicinttrig",
            "clicintip",
            "clicintie",
            "clicintattr",
            "clicintctl",
        )
        # This is dangerous, but since we know what we are adding it's fine

        # We have some registers that are mapped in quad mode, and some that are mapped in direct mode
        # The quad mapped registers occur in order reg1,reg2,reg3,reg4,reg1,reg2,reg3,reg4,reg1,reg2,reg3,reg4,reg1,reg2,reg3,reg4
        # The first register that is quad mapped is clicintip, which is at address 0x1000 all addresses after that are quad mapped
        # All addresses before that are direct mapped

        # Pre map write data, this is common for all regs
        for reg in self.regs:
            m.d.comb += [reg.write_data.eq(self.write_data)]
        # Case 1: Direct mapped
        with m.Switch(self.is_quad_mapped):
            with m.Case(0):
                # Switch on the register address
                # Start addresses are as follows:
                # CLICCFG = 0x0000
                # CLICINFO = 0x0004
                # CLICINTTRIG = 0x0040
                a = self.BaseAddresses
                addresses = [a.CLICCFG, a.CLICINFO.value, a.CLICINTTRIG.value]
                self.is_cliccfg = is_cliccfg = Signal()
                self.is_clicinfo = is_clicinfo = Signal()
                self.is_clicinttrig = is_clicinttrig = Signal()
                addr = self.address
                m.d.comb += [
                    is_cliccfg.eq(
                        (addr >= a.CLICCFG.value) * (addr < a.CLICINFO.value)
                    ),
                    is_clicinfo.eq(
                        (addr >= a.CLICINFO.value) * (addr < a.CLICINTTRIG.value)
                    ),
                    is_clicinttrig.eq(
                        (addr >= a.CLICINTTRIG.value) * (addr < a.CLICINTIP.value)
                    ),
                ]
                self.reg = reg = Signal(3)
                m.d.comb += [
                    reg[0].eq(is_cliccfg),
                    reg[1].eq(is_clicinfo),
                    reg[2].eq(is_clicinttrig),
                ]
                with m.Switch(reg):
                    with m.Case(0b001):
                        # This is cliccfg
                        m.d.comb += [
                            # * Inputs
                            self.cliccfg.write_enable.eq(self.write_enable),
                            self.cliccfg.address.eq(self.address),
                            self.cliccfg.reset.eq(self.reset),
                            # * Outputs
                            self.read_data.eq(self.cliccfg.read_data),
                        ]
                    with m.Case(0b010):
                        # This is clicinfo
                        m.d.comb += [
                            # * Inputs
                            self.clicinfo.write_enable.eq(self.write_enable),
                            self.clicinfo.address.eq(self.address),
                            self.clicinfo.reset.eq(self.reset),
                            # * Outputs
                            self.read_data.eq(self.clicinfo.read_data),
                        ]
                    with m.Case(0b100):
                        # This is clicinttrig
                        m.d.comb += [
                            # * Inputs
                            self.clicinttrig.write_enable.eq(self.write_enable),
                            self.clicinttrig.address.eq(self.address),
                            self.clicinttrig.reset.eq(self.reset),
                            # * Outputs
                            self.read_data.eq(self.clicinttrig.read_data),
                        ]
            # Case 2: Quad mapped
            with m.Case(1):
                self.address_intermediate = address = Signal.like(self.address)
                self.lsbs = Signal(2)
                self.relative_addr = relative_addr = Signal.like(self.address)

                # Switch on the register address % 4
                # Start addresses are as follows:
                # CLICINTIP = 0x1000
                # CLICINTIE = 0x1001
                # CLICINTATTR = 0x1002
                # CLICINTCTL = 0x1003
                # The % 4 is the 2 LSBs of the address
                m.d.comb += relative_addr.eq(
                    self.address - self.BaseAddresses.CLICINTIP.value
                )
                m.d.comb += self.lsbs.eq(relative_addr[0:2])
                m.d.comb += address.eq(self.relative_addr - self.lsbs)

                with m.Switch(self.lsbs):
                    with m.Case(0):
                        m.d.comb += [
                            # * Inputs
                            self.clicintip.write_enable.eq(self.write_enable),
                            self.clicintip.address.eq(address),
                            self.clicintip.reset.eq(self.reset),
                            # * Outputs
                            self.read_data.eq(self.clicintip.read_data),
                        ]
                    with m.Case(1):
                        m.d.comb += [
                            # * Inputs
                            self.clicintie.write_enable.eq(self.write_enable),
                            self.clicintie.address.eq(address),
                            self.clicintie.reset.eq(self.reset),
                            # * Outputs
                            self.read_data.eq(self.clicintie.read_data),
                        ]
                    with m.Case(2):
                        m.d.comb += [
                            # * Inputs
                            self.clicintattr.write_enable.eq(self.write_enable),
                            self.clicintattr.address.eq(address),
                            self.clicintattr.reset.eq(self.reset),
                            # * Outputs
                            self.read_data.eq(self.clicintattr.read_data),
                        ]
                        # We can't have more than one write at a time.
                    with m.Case(3):
                        m.d.comb += [
                            # * Inputs
                            self.clicintctl.write_enable.eq(self.write_enable),
                            self.clicintctl.address.eq(address),
                            self.clicintctl.reset.eq(self.reset),
                            # * Outputs
                            self.read_data.eq(self.clicintctl.read_data),
                        ]
                        # We can't have more than one write at a time.

        return m
