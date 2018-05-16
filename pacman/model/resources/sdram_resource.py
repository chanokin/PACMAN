from .abstract_sdram import AbstractSDRAM


class SDRAMResource(AbstractSDRAM):
    """ DEPRICATED: Please use SDRAMAvaiable, ConstantSDRAM or VariableSDRAM
    """

    __slots__ = [
        # The amount of SDRAM in bytes
        "_sdram"
    ]

    def __init__(self, sdram):
        """
        :param sdram: The amount of SDRAM in bytes
        :type sdram: int
        :raise None: No known exceptions are raised
        """
        self._sdram = sdram

    def get_total_sdram(self):
        return self._sdram
