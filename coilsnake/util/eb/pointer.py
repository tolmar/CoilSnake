import logging
from coilsnake.exceptions.common.exceptions import InvalidArgumentError

log = logging.getLogger(__name__)


def from_snes_address(address):
    if address < 0:
        raise InvalidArgumentError("Invalid snes address[{:#x}]".format(address))
    elif address >= 0xc00000:
        return address - 0xc00000
    else:
        return address


def to_snes_address(address):
    if address >= 0x400000:
        return address
    else:
        return address + 0xc00000


def read_asm_pointer(block, offset):
    part1 = block[offset + 1] | (block[offset + 2] << 8)
    part2 = block[offset + 6] | (block[offset + 7] << 8)
    return part1 | (part2 << 16)


def write_asm_pointer(block, offset, pointer):
    block[offset + 1] = pointer & 0xff
    block[offset + 2] = (pointer >> 8) & 0xff
    block[offset + 6] = (pointer >> 16) & 0xff
    block[offset + 7] = (pointer >> 24) & 0xff

def write_xl_pointer(block, offset, pointer):
    block[offset + 1] = pointer & 0xff
    block[offset + 2] = (pointer >> 8) & 0xff
    block[offset + 3] = (pointer >> 16) & 0xff

# Reference to a location in ROM that uses LDA_a STA_d LDA_a STA_d or equivalent
# to load a pointer.
class AsmPointerReference(object):
    def __init__(self, offset):
        self.offset = offset

    def write(self, rom, address):
        log.info("Writing pointer at " + hex(self.offset))
        write_asm_pointer(rom, self.offset, address)

# Reference to a location in the ROM that uses LDA_xl or similar instructions.
class XlPointerReference(object):
    # Adjustment is added to the value at the ROM value when writing, subtracted
    # when reading. Because they've read a long pointer using one of these.
    def __init__(self, offset, adjustment = 0):
        self.offset = offset
        self.adjustment = adjustment

    def write(self, rom, address):
        log.info("Writing xl pointer at " + hex(self.offset))
        write_xl_pointer(rom, self.offset, address + self.adjustment)

    def read(self, rom):
        return rom.read_multi(self.offset, 3) - self.adjustment

# Reference to a location in ROM that saves the bank byte of a pointer.
class BankByteReference(object):
    def __init__(self, offset):
        self.offset = offset

    def write(self, rom, address):
        log.info("Writing bank byte at " + hex(self.offset))
        rom[self.offset] = (address >> 16) & 0xff

# Reference to a location in ROM that saves the low two bytes of a pointer.
class ShortPointerReference(object):
    def __init__(self, offset, adjustment = 0):
        self.offset = offset
        self.adjustment = adjustment

    def write(self, rom, address):
        log.info("Writing short pointer at " + hex(self.offset))
        address = address + self.adjustment
        rom[self.offset] = address & 0xff
        rom[self.offset + 1] = (address >> 8) & 0xff
