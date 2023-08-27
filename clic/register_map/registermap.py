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

    @info(type=InfoType.MODULE, module="RegisterMap")
    def __init__(
        self,
    ):
        self.address = Signal(32)
        self.write_data = Signal(32)
        self.write_enable = Signal()
        self.read_data = Signal(32)

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
        # * Generic 4096 registers
        reg_4096 = lambda name, details: RegisterFile(
            register_count=4096,
            register_width=1,
            register_type=RegisterType.READ_WRITE,
            initial_values=lambda _: 0x00,
            file_name=name,
            file_description=details,
            start_address=0x0,  # Has to be remapped in this module
            bounds_check=True,  # No need to check bounds, as that is handled by this module
        )

        # * clicintip
        self.clicintip = reg_4096("clicintip", "CLIC interrupt pending register")
        # * clicintie
        self.clicintie = reg_4096("clicintie", "CLIC interrupt enable register")
        # * clicintattr
        self.clicintattr = reg_4096("clicintattr", "CLIC interrupt attribute register")
        # * clicintctl
        self.clicintctl = reg_4096("clicintctl", "CLIC interrupt control register")

    def ports(self):
        return [
            self.address,
            self.write_data,
            self.write_enable,
            self.read_data,
        ]

    def elaborate(self, platform):
        m = Module()

        # Create intermediate signals for pure memory mapped registers
        addr, _, en, read = [Signal().like(signal) for signal in self.ports()]
        write_data_8b = Signal(8)
        quad_addr = Signal.like(self.address)
        read_intermediate = Signal.like(self.read_data)
        is_quad_mapped = Signal()
        register = Signal(2)

        m.d.comb += [
            en.eq(0x0),
        ]
        m.d.comb += is_quad_mapped.eq(self.address >= 0x1000)
        m.d.comb += register.eq(self.address[-2:])  # 2 LSBs
        m.d.comb += quad_addr.eq(
            (self.address - self.BaseAddresses.CLICINTIP.value) >> 2
        )

        # * cliccfg
        m.submodules.cliccfg = cliccfg = self.cliccfg
        # * clicinfo
        m.submodules.clicinfo = clicinfo = self.clicinfo
        # * clicinttrig
        m.submodules.clicinttrig = clicinttrig = self.clicinttrig
        # * clicintip
        m.submodules.clicintip = clicintip = self.clicintip
        # * clicintie
        m.submodules.clicintie = clicintie = self.clicintie
        # * clicintattr
        m.submodules.clicintattr = clicintattr = self.clicintattr
        # * clicintctl
        m.submodules.clicintctl = clicintctl = self.clicintctl

        # direct_mapped = [cliccfg, clicinfo, clicinttrig]
        # quad_mapped = [clicintip, clicintie, clicintattr, clicintctl]

        m.d.comb += write_data_8b.eq(self.write_data[8:])

        # We have some registers that are mapped in quad mode, and some that are mapped in direct mode
        # The quad mapped registers occur in order reg1,reg2,reg3,reg4,reg1,reg2,reg3,reg4,reg1,reg2,reg3,reg4,reg1,reg2,reg3,reg4
        # The first register that is quad mapped is clicintip, which is at address 0x1000 all addresses after that are quad mapped
        # All addresses before that are direct mapped

        # Case 1: Direct mapped
        with m.If(~is_quad_mapped):
            # Switch on the register address
            # Start addresses are as follows:
            # CLICCFG = 0x0000
            # CLICINFO = 0x0004
            # CLICINTTRIG = 0x0040

            # * cliccfg
            with m.If(
                (self.address >= self.BaseAddresses.CLICCFG.value)
                * (self.address < self.BaseAddresses.CLICINFO.value)
            ):
                m.d.comb += [
                    cliccfg.write_data.eq(self.write_data),
                    cliccfg.write_enable.eq(self.write_enable),
                    cliccfg.address.eq(self.address),
                    self.read_data.eq(cliccfg.read_data),
                ]
            # * clicinfo
            with m.Elif(
                (self.address >= self.BaseAddresses.CLICINFO.value)
                * (self.address < self.BaseAddresses.CLICINTTRIG.value)
            ):
                m.d.comb += [
                    clicinfo.write_data.eq(self.write_data),
                    clicinfo.write_enable.eq(self.write_enable),
                    clicinfo.address.eq(self.address),
                    self.read_data.eq(clicinfo.read_data),
                ]
            # * clicinttrig
            with m.Elif(
                (self.address >= self.BaseAddresses.CLICINTTRIG.value)
                * (self.address < self.BaseAddresses.CLICINTIP.value)
            ):
                m.d.comb += [
                    clicinttrig.write_data.eq(self.write_data),
                    clicinttrig.write_enable.eq(self.write_enable),
                    clicinttrig.address.eq(self.address),
                    self.read_data.eq(clicinttrig.read_data),
                ]
        # Case 2: Quad mapped
        with m.Else():
            relative_addr = Signal.like(self.address)
            m.d.comb += relative_addr.eq(
                self.address - self.BaseAddresses.CLICINTIP.value
            )
            # Switch on the register address % 4
            # Start addresses are as follows:
            # CLICINTIP = 0x1000
            # CLICINTIE = 0x1001
            # CLICINTATTR = 0x1002
            # CLICINTCTL = 0x1003
            # The % 4 is the 2 LSBs of the address
            lsbs = Signal(2)
            m.d.comb += lsbs.eq(relative_addr[0:2])
            # * clicintip
            with m.If(lsbs == 0):
                m.d.comb += [
                    clicintip.write_data.eq(self.write_data),
                    clicintip.write_enable.eq(self.write_enable),
                    clicintip.address.eq(self.address),
                    self.read_data.eq(clicintip.read_data),
                ]
            # * clicintie
            with m.Elif(lsbs == 1):
                m.d.comb += [
                    clicintie.write_data.eq(self.write_data),
                    clicintie.write_enable.eq(self.write_enable),
                    clicintie.address.eq(self.address),
                    self.read_data.eq(clicintie.read_data),
                ]
            # * clicintattr
            with m.Elif(lsbs == 2):
                m.d.comb += [
                    clicintattr.write_data.eq(self.write_data),
                    clicintattr.write_enable.eq(self.write_enable),
                    clicintattr.address.eq(self.address),
                    self.read_data.eq(clicintattr.read_data),
                ]
            # * clicintctl
            with m.Elif(lsbs == 3):
                m.d.comb += [
                    clicintctl.write_data.eq(self.write_data),
                    clicintctl.write_enable.eq(self.write_enable),
                    clicintctl.address.eq(self.address),
                    self.read_data.eq(clicintctl.read_data),
                ]

        """



        for reg in direct_mapped:
            m.d.comb += [
                reg.write_data.eq(self.write_data),
            ]

        for reg in quad_mapped:
            m.d.comb += reg.address.eq(quad_addr)
            m.d.comb += reg.write_data.eq(write_data_8b)
        # Given that the
        is_cliccfg, is_clicinfo, is_clicinttrig = [Signal(1) for _ in range(3)]
        m.d.comb += [
            is_cliccfg.eq(cliccfg.is_for_me & ~cliccfg._out_of_bounds),
            is_clicinfo.eq(clicinfo.is_for_me & ~clicinfo._out_of_bounds),
            is_clicinttrig.eq(clicinttrig.is_for_me & ~clicinttrig._out_of_bounds),
        ]

        # Check if address is clicintip[0] or larger

        with m.If(is_quad_mapped):
            zeros = Signal(32 - clicintip.read_data.width)
            m.d.comb += zeros.eq(0x0)
            with m.Switch(register):
                lookup = ["clicintip", "clicintie", "clicintattr", "clicintctl"]
                for i in range(4):
                    exec(
                        f""with m.Case(0b{i:02b}):
                                m.d.comb += read_intermediate.eq(Cat(zeros, clicintip.read_data))
                                m.d.comb += {lookup[i]}.write_enable.eq(self.write_enable)
                                m.d.comb += {lookup[i]}.write_data.eq(self.write_data)
                         "",
                        globals(),
                        locals(),
                    )
        with m.Else():
            lookup = ["cliccfg", "clicinfo", "clicinttrig"]

            m.d.comb += [
                addr.eq(self.address),
            ]
            with m.If(is_cliccfg):
                m.d.comb += [
                    cliccfg.write_enable.eq(self.write_enable),
                    cliccfg.write_data.eq(self.write_data),
                    cliccfg.address.eq(self.address),
                    read_intermediate.eq(cliccfg.read_data),
                ]
            with m.Elif(is_clicinfo):
                m.d.comb += [
                    clicinfo.write_enable.eq(self.write_enable),
                    clicinfo.write_data.eq(self.write_data),
                    clicinfo.address.eq(self.address),
                    read_intermediate.eq(clicinfo.read_data),
                ]
            with m.Elif(is_clicinttrig):
                m.d.comb += [
                    clicinttrig.write_enable.eq(self.write_enable),
                    clicinttrig.write_data.eq(self.write_data),
                    clicinttrig.address.eq(self.address),
                    read_intermediate.eq(clicinttrig.read_data),
                ]

        m.d.comb += [
            self.read_data.eq(read_intermediate),
        ]
        """
        return m
