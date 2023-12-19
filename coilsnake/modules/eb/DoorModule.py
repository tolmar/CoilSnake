import logging

from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.doors import door_from_block, door_from_yml_rep, not_in_destination_bank
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import convert_values_to_hex_repr, yml_load, yml_dump
from coilsnake.util.eb.pointer import to_snes_address, from_snes_address, AsmPointerReference

from collections import OrderedDict

log = logging.getLogger(__name__)

DOOR_TABLE_REFERENCES = [
    AsmPointerReference(from_snes_address(0xC07486)),
]

def sort_yml_doors(arg): # Reorder dicts
    if isinstance(arg, list):
        return [sort_yml_doors(v) for v in arg]

    if isinstance(arg, dict):
        return OrderedDict((k, sort_yml_doors(arg[k])) for k in sorted(arg.keys()))

    return arg

class DoorModule(EbModule):
    NAME = "Doors"

    FREE_RANGES = [
        # Door pointer table
        (from_snes_address(0xD00000), from_snes_address(0xD00000 + 1280 * 4 - 1)),
        # Actual door data is freed in write_to_rom, see note there
    ]

    def __init__(self):
        super(EbModule, self).__init__()
        self.pointer_table = eb_table_from_offset(0xD00000)
        self.door_areas = []

    def read_from_rom(self, rom):
        self.pointer_table.from_block(rom, from_snes_address(0xD00000))
        self.door_areas = []
        for i in range(self.pointer_table.num_rows):
            offset = from_snes_address(self.pointer_table[i][0])
            door_area = []
            num_doors = rom.read_multi(offset, 2)
            offset += 2
            for j in range(num_doors):
                door = door_from_block(rom, offset)
                if door is None:
                    # If we've found an invalid door, stop reading from this door group.
                    # This is expected, since a clean ROM contains some invalid doors.
                    break
                door_area.append(door)
                offset += 5
            self.door_areas.append(door_area)

    def write_to_project(self, resourceOpener):
        out = dict()
        x = y = 0
        rowOut = dict()
        for entry in self.door_areas:
            if not entry:
                rowOut[x % 32] = None
            else:
                rowOut[x % 32] = [z.yml_rep() for z in entry]
            if (x % 32) == 31:
                # Start new row
                out[y] = rowOut
                x = 0
                y += 1
                rowOut = dict()
            else:
                x += 1

        with resourceOpener("map_doors", "yml", True) as f:
            s = yml_dump(
                out,
                default_flow_style=False)
            s = convert_values_to_hex_repr(yml_str_rep=s, key="Event Flag")
            f.write(s)

    def read_from_project(self, resourceOpener):
        self.door_areas = []
        with resourceOpener("map_doors", "yml", True) as f:
            input = sort_yml_doors(yml_load(f))
            for y in input:
                row = input[y]
                for x in row:
                    if row[x] is None:
                        self.door_areas.append(None)
                    else:
                        entry = []
                        for door in row[x]:
                            d = door_from_yml_rep(door)
                            entry.append(d)
                        self.door_areas.append(entry)

    def write_to_rom(self, rom):
        # Create new pointer table
        pointer_table = Block(len(self.door_areas) * 4)
        # Deallocate the range of the ROM in which we will write the door destinations.
        # We deallocate it here instead of specifying it in FREE_RANGES because we want to be sure that this module
        # get first dibs at writing to this range. This is because door destinations needs to be written to the 0x0F
        # bank of the EB ROM, and this is one of the few ranges available in that bank.
        # NOTE: you could fix this by repointing all the references to what ebsrc calls DOOR_DATA,
        # but you'll still need to make sure all the doors end up in the same bank.
        rom.deallocate((0x0F0000, 0x0F58EE))
        destination_offsets = dict()
        empty_area_offset = to_snes_address(rom.allocate(data=[0, 0], can_write_to=not_in_destination_bank))
        i = 0
        for door_area in self.door_areas:
            if (door_area is None) or (not door_area):
                pointer_table.write_multi(i * 4, empty_area_offset, 4)
            else:
                num_doors = len(door_area)
                area_offset = rom.allocate(size=(2 + num_doors * 5), can_write_to=not_in_destination_bank)
                pointer_table.write_multi(i * 4, to_snes_address(area_offset), 4)
                rom.write_multi(area_offset, num_doors, 2)
                area_offset += 2
                for door in door_area:
                    door.write_to_block(rom, area_offset, destination_offsets)
                    area_offset += 5
            i += 1
        # Write pointer table
        pointer_addr = rom.allocate(data=pointer_table)
        for pointer in DOOR_TABLE_REFERENCES:
            pointer.write(rom, to_snes_address(pointer_addr))
        log.debug("Door pointers @ " + hex(to_snes_address(pointer_addr)))
