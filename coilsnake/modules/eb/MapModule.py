import yaml
import logging

from coilsnake.model.common.blocks import Block
from coilsnake.model.common.table import EnumeratedLittleEndianIntegerTableEntry, LittleEndianIntegerTableEntry, \
    RowTableEntry
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import replace_field_in_yml, yml_load
from coilsnake.util.eb.pointer import to_snes_address, from_snes_address, AsmPointerReference, XlPointerReference, BankByteReference, ShortPointerReference

log = logging.getLogger(__name__)

# Size of a map chunk in bytes
MAP_CHUNK_SIZE = 10240
# Size of map chunk in tile rows
MAP_CHUNK_HEIGHT = 40
# Code references to the main map chunk pointers table
MAP_POINTERS_REFERENCES = [
    XlPointerReference(from_snes_address(0xC0A1DA)),
    XlPointerReference(from_snes_address(0xC0A1E0), 2)
]
# Code references to the last two map chunks (used for high bits of tiles).
# Despite being in the pointers table, these are never actually read from the
# pointers table. The game also assumes these are in the same bank as eachother;
# for convenience sake I'm just making them contiguous.
TAIL_CHUNKS_REFERENCES = [
    BankByteReference(from_snes_address(0xC0A18E)),
    ShortPointerReference(from_snes_address(0xC0A193))
]
# Need to keep an eye on this one separately, since it's the second tail chunk
TAIL_CHUNK_2_REFERENCES = [
    ShortPointerReference(from_snes_address(0xC0A19D))
]
# Shorts referring to map bounds checks
MAP_SIZE_BOUNDS_CHECKS = [
    from_snes_address(0xC00B41 + 1),
    from_snes_address(0xC00C8D + 1),
]

SECTOR_TILESETS_PALETTES_REFERENCES = [
    XlPointerReference(from_snes_address(0xC008F7)),
    XlPointerReference(from_snes_address(0xC00B24)),
    XlPointerReference(from_snes_address(0xC00B6F)),
    XlPointerReference(from_snes_address(0xC00C35)),
    XlPointerReference(from_snes_address(0xC00C7F)),
    XlPointerReference(from_snes_address(0xC02303)),
    XlPointerReference(from_snes_address(0xC02777)),
    XlPointerReference(from_snes_address(0xC4DFF5)),
    AsmPointerReference(from_snes_address(0xC4E163))
]

SECTOR_MUSIC_TABLE_REFERENCES = [
    XlPointerReference(from_snes_address(0xC06921)),
    XlPointerReference(from_snes_address(0xEFDDB8))
]

MAP_MISC_TABLE_REFERENCES = [
    XlPointerReference(from_snes_address(0xC00ABC)),
    XlPointerReference(from_snes_address(0xC026CD))
]

TOWN_MAP_TABLE_REFERENCES = [
    XlPointerReference(from_snes_address(0xC4D29F)),
    AsmPointerReference(from_snes_address(0xC4D30C))
]

# Weirdly labeled reference to tail chunk data
LOCAL_TILESETS_OFFSET = 0x175000
MAP_HEIGHT = 320
MAP_WIDTH = 256

SECTOR_TILESETS_PALETTES_TABLE_OFFSET = 0xD7A800
SECTOR_MUSIC_TABLE_OFFSET = 0xDCD637
SECTOR_MISC_TABLE_OFFSET = 0xD7B200
SECTOR_TOWN_MAP_TABLE_OFFSET = 0xEFA70F

TELEPORT_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Teleport", 1, ["Enabled", "Disabled"]
)
TOWNMAP_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Town Map", 1,
    ["None", "Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers", "None 2"]
)
SETTING_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Setting", 1,
    ["None", "Indoors", "Exit Mouse usable", "Lost Underworld sprites", "Magicant sprites", "Robot sprites",
     "Butterflies", "Indoors and Butterflies"]
)
TOWNMAP_IMAGE_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Town Map Image", 1,
    ["None", "Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers"]
)
TOWNMAP_ARROW_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Town Map Arrow", 1,
    ["None", "Up", "Down", "Right", "Left"]
)
TOWNMAP_X = LittleEndianIntegerTableEntry.create("Town Map X", 1)
TOWNMAP_Y = LittleEndianIntegerTableEntry.create("Town Map Y", 1)

SectorYmlTable = RowTableEntry.from_schema(
    name="Aggregate Sector Properties Table Entry",
    schema=[LittleEndianIntegerTableEntry.create("Tileset", 1),
            LittleEndianIntegerTableEntry.create("Palette", 1),
            LittleEndianIntegerTableEntry.create("Music", 1),
            TELEPORT_ENTRY,
            TOWNMAP_ENTRY,
            SETTING_ENTRY,
            LittleEndianIntegerTableEntry.create("Item", 1),
            TOWNMAP_ARROW_ENTRY,
            TOWNMAP_IMAGE_ENTRY,
            TOWNMAP_X,
            TOWNMAP_Y]
)


class MapModule(EbModule):
    NAME = "Map"
    FREE_RANGES = [
        # Tile chunk data
        (from_snes_address(0xD60000), from_snes_address(0xD7A800 - 1)),
        # Tile chunk pointer table
        (from_snes_address(0xC42F64), from_snes_address(0xC42F64 + 39)),
        # Sector tilesets and palettes data
        (from_snes_address(0xD7A800), from_snes_address(0xD7A800 + 2559)),
        # Sector music
        (from_snes_address(0xDCD637), from_snes_address(0xDCD637 + 2559)),
        # Sector misc
        (from_snes_address(0xD7B200), from_snes_address(0xD7B200 + 2559)),
        # Sector town map
        (from_snes_address(0xEFA70F), from_snes_address(0xEFA70F + 2559))
    ]

    def __init__(self):
        super(MapModule, self).__init__()
        self.tiles = []
        self.sector_tilesets_palettes_table = eb_table_from_offset(offset=SECTOR_TILESETS_PALETTES_TABLE_OFFSET,
                                                                   name="map_sectors")
        self.sector_music_table = eb_table_from_offset(offset=SECTOR_MUSIC_TABLE_OFFSET,
                                                       name="map_sectors")
        self.sector_misc_table = eb_table_from_offset(offset=SECTOR_MISC_TABLE_OFFSET,
                                                      name="map_sectors")
        self.sector_town_map_table = eb_table_from_offset(offset=SECTOR_TOWN_MAP_TABLE_OFFSET,
                                                          name="map_sectors")
        self.sector_yml_table = eb_table_from_offset(offset=SECTOR_TILESETS_PALETTES_TABLE_OFFSET,
                                                     single_column=SectorYmlTable,
                                                     num_rows=self.sector_tilesets_palettes_table.num_rows,
                                                     name="map_sectors")

    def read_from_rom(self, rom):
        # Read map data
        map_ptrs_addr = from_snes_address(MAP_POINTERS_REFERENCES[0].read(rom))
        map_addrs = [from_snes_address(rom.read_multi(map_ptrs_addr + x * 4, 4)) for x in range(8)]

        def read_row_data(row_number):
            offset = map_addrs[row_number % 8] + ((row_number >> 3) << 8)
            return rom[offset:offset + MAP_WIDTH].to_list()

        self.tiles = list(map(read_row_data, range(MAP_HEIGHT)))
        k = LOCAL_TILESETS_OFFSET
        for i in range(MAP_HEIGHT >> 3):
            for j in range(MAP_WIDTH):
                self.tiles[i << 3][j] |= (rom[k] & 3) << 8
                self.tiles[(i << 3) | 1][j] |= ((rom[k] >> 2) & 3) << 8
                self.tiles[(i << 3) | 2][j] |= ((rom[k] >> 4) & 3) << 8
                self.tiles[(i << 3) | 3][j] |= ((rom[k] >> 6) & 3) << 8
                self.tiles[(i << 3) | 4][j] |= (rom[k + 0x3000] & 3) << 8
                self.tiles[(i << 3) | 5][j] |= ((rom[k + 0x3000] >> 2) & 3) << 8
                self.tiles[(i << 3) | 6][j] |= ((rom[k + 0x3000] >> 4) & 3) << 8
                self.tiles[(i << 3) | 7][j] |= ((rom[k + 0x3000] >> 6) & 3) << 8
                k += 1

        # Read sector data
        self.sector_tilesets_palettes_table.from_block(rom, from_snes_address(SECTOR_TILESETS_PALETTES_TABLE_OFFSET))
        self.sector_music_table.from_block(rom, from_snes_address(SECTOR_MUSIC_TABLE_OFFSET))
        self.sector_misc_table.from_block(rom, from_snes_address(SECTOR_MISC_TABLE_OFFSET))
        self.sector_town_map_table.from_block(rom, from_snes_address(SECTOR_TOWN_MAP_TABLE_OFFSET))

    def write_to_rom(self, rom):
        # Write tile data to the blocks
        map_height = len(self.tiles)
        chunk_size = 256 * int(map_height / 8)
        log.debug("Tile chunk size #{}".format(chunk_size))
        tile_blocks = [Block(chunk_size) for i in range(8)]
        for i in range(map_height):
            chunk = i % 8
            offset = ((i >> 3) << 8)
            tile_blocks[chunk][offset:offset + MAP_WIDTH] = [x & 0xff for x in self.tiles[i]]
        # Write data to the tail blocks
        tail_block = Block(chunk_size * 2)
        k = 0
        for i in range(map_height >> 3):
            for j in range(MAP_WIDTH):
                c = ((self.tiles[i << 3][j] >> 8)
                     | ((self.tiles[(i << 3) | 1][j] >> 8) << 2)
                     | ((self.tiles[(i << 3) | 2][j] >> 8) << 4)
                     | ((self.tiles[(i << 3) | 3][j] >> 8) << 6))
                tail_block[k] = c
                c = ((self.tiles[(i << 3) | 4][j] >> 8)
                     | ((self.tiles[(i << 3) | 5][j] >> 8) << 2)
                     | ((self.tiles[(i << 3) | 6][j] >> 8) << 4)
                     | ((self.tiles[(i << 3) | 7][j] >> 8) << 6))
                # Interestingly, vanilla used 0x200 more than it needed here
                tail_block[k + chunk_size] = c
                k += 1
        # Allocate the blocks
        tile_block_addrs = [rom.allocate(data=tile_blocks[i]) for i in range(8)]
        tail_block_addr = rom.allocate(data=tail_block)
        # Write the pointer table
        map_pointers = Block(4 * 8)
        for i in range(8):
            log.debug("Tile block addr @ " + hex(to_snes_address(tile_block_addrs[i])))
            map_pointers.write_multi(i * 4, to_snes_address(tile_block_addrs[i]), 4)
        log.debug("Tail block addr @ " + hex(to_snes_address(tail_block_addr)))
        # Allocate the pointer table
        map_pointers_addr = rom.allocate(data=map_pointers)
        log.debug("Map pointers addr @ " + hex(to_snes_address(map_pointers_addr)))
        # Update references to the data
        for pointer in MAP_POINTERS_REFERENCES:
            pointer.write(rom, to_snes_address(map_pointers_addr))
        for pointer in TAIL_CHUNKS_REFERENCES:
            pointer.write(rom, to_snes_address(tail_block_addr))
        for pointer in TAIL_CHUNK_2_REFERENCES:
            pointer.write(rom, to_snes_address(tail_block_addr + chunk_size))

        # Update this bounds check to whatever the new map size is
        for pointer in MAP_SIZE_BOUNDS_CHECKS:
            rom.write_multi(pointer, map_height, 2)

        # Write sector data
        self._write_sector_table(rom, self.sector_tilesets_palettes_table, SECTOR_TILESETS_PALETTES_REFERENCES)
        self._write_sector_table(rom, self.sector_music_table, SECTOR_MUSIC_TABLE_REFERENCES)
        self._write_sector_table(rom, self.sector_misc_table, MAP_MISC_TABLE_REFERENCES)
        self._write_sector_table(rom, self.sector_town_map_table, TOWN_MAP_TABLE_REFERENCES)

    def _write_sector_table(self, rom, table, references):
        new_pointer = rom.allocate(size=table.size)
        table.to_block(rom, new_pointer)
        for pointer in references:
            pointer.write(rom, to_snes_address(new_pointer))

    def write_to_project(self, resource_open):
        # Write map tiles
        with resource_open("map_tiles", "map", True) as f:
            for row in self.tiles:
                f.write(hex(row[0])[2:].zfill(3))
                for tile in row[1:]:
                    f.write(" ")
                    f.write(hex(tile)[2:].zfill(3))
                f.write("\n")

        for i in range(self.sector_yml_table.num_rows):
            tileset = self.sector_tilesets_palettes_table[i][0] >> 3
            palette = self.sector_tilesets_palettes_table[i][0] & 7
            music = self.sector_music_table[i][0]
            teleport = self.sector_misc_table[i][0] >> 7
            townmap = (self.sector_misc_table[i][0] >> 3) & 7
            setting = self.sector_misc_table[i][0] & 7
            item = self.sector_misc_table[i][1]
            townmap_arrow = self.sector_town_map_table[i][0] >> 4
            townmap_image = self.sector_town_map_table[i][0] & 0xf
            townmap_x = self.sector_town_map_table[i][1]
            townmap_y = self.sector_town_map_table[i][2]

            self.sector_yml_table[i] = [
                tileset,
                palette,
                music,
                teleport,
                townmap,
                setting,
                item,
                townmap_arrow,
                townmap_image,
                townmap_x,
                townmap_y
            ]
        with resource_open("map_sectors", "yml", True) as f:
            self.sector_yml_table.to_yml_file(f)

    def read_from_project(self, resource_open):
        # Read map data
        with resource_open("map_tiles", "map", True) as f:
            self.tiles = [[int(x, 16) for x in y.split(" ")] for y in f.readlines()]

        # Open the sectors file first and see how expanded it is
        with resource_open("map_sectors", "yml", True) as f:
            # TODO: this invocation (copied from ExpandedTablesModule) is weird.
            # A helper method would help, but I think that too is just a bandaid
            # on how strange it is that from_yml_file has a mystery max-length
            # setting it pulls out of in eb.yml
            yml_rep = yml_load(f)
            num_rows = len(yml_rep)
            self.sector_yml_table.recreate(num_rows=num_rows)
            self.sector_yml_table.from_yml_rep(yml_rep)
            # TODO: okay yeah this is scuffed; I have to resize them all
            self.sector_tilesets_palettes_table.recreate(num_rows = num_rows)
            self.sector_music_table.recreate(num_rows = num_rows)
            self.sector_misc_table.recreate(num_rows = num_rows)
            self.sector_town_map_table.recreate(num_rows = num_rows)

        for i in range(self.sector_yml_table.num_rows):
            tileset = self.sector_yml_table[i][0]
            palette = self.sector_yml_table[i][1]
            music = self.sector_yml_table[i][2]
            teleport = self.sector_yml_table[i][3]
            townmap = self.sector_yml_table[i][4]
            setting = self.sector_yml_table[i][5]
            item = self.sector_yml_table[i][6]
            townmap_arrow = self.sector_yml_table[i][7]
            townmap_image = self.sector_yml_table[i][8]
            townmap_x = self.sector_yml_table[i][9]
            townmap_y = self.sector_yml_table[i][10]

            self.sector_tilesets_palettes_table[i] = [(tileset << 3) | palette]

            self.sector_music_table[i] = [music]

            self.sector_misc_table[i] = [(teleport << 7) | (townmap << 3) | setting, item]

            self.sector_town_map_table[i] = [((townmap_arrow << 4) | (townmap_image & 0xf)),
                                             townmap_x,
                                             townmap_y]

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version <= 2:
            replace_field_in_yml(resource_name="map_sectors",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Town Map",
                                 value_map={"scummers": "summers"})

            self.read_from_rom(rom)

            with resource_open_r("map_sectors", 'yml', True) as f:
                data = yml_load(f)
                for i in data:
                    data[i]["Town Map Image"] = TOWNMAP_IMAGE_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] & 0xf)
                    data[i]["Town Map Arrow"] = TOWNMAP_ARROW_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] >> 4)
                    data[i]["Town Map X"] = TOWNMAP_X.to_yml_rep(self.sector_town_map_table[i][1])
                    data[i]["Town Map Y"] = TOWNMAP_Y.to_yml_rep(self.sector_town_map_table[i][2])
            with resource_open_w("map_sectors", 'yml', True) as f:
                yaml.dump(data, f, Dumper=yaml.CSafeDumper, default_flow_style=False)

            self.upgrade_project(3, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
