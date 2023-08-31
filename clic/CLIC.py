from amaranth import Elaboratable
from clic.register_map import RegisterMap, RegisterFile


class CLIC(Elaboratable):
    """
    Defines the Core Local Interrupt Controller (CLIC) module.
    """

    def __init__(self):
        """
        Initializes the CLIC module.
        """
        pass

    def elaborate(self, *_):
        """
        Builds the CLIC module.
        """
        pass

    def __repr__(self):
        return "<CLIC>"

    def __str__(self):
        return repr(self)


if __name__ == "__main__":
    pass
