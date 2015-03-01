from model.eb.table import EbStandardNullTerminatedTextTableEntry, EbStandardTextTableEntry
from modules.eb.EbModule import EbModule
from util.common.yml import yml_load, yml_dump
from util.eb.pointer import read_asm_pointer, from_snes_address, write_asm_pointer, to_snes_address


class EbMiscTextAsmPointer(object):
    def __init__(self, asm_pointer_loc):
        self.asm_pointer_loc = asm_pointer_loc

    def read(self, block):
        return from_snes_address(read_asm_pointer(block, self.asm_pointer_loc))

    def write(self, block, address):
        write_asm_pointer(block=block, offset=self.asm_pointer_loc, pointer=address)


class EbMiscTextString(object):
    def __init__(self, pointer=None, default_offset=None, maximum_size=None, null_terminated=False):
        if pointer and default_offset:
            raise ValueError("Only one of pointer and default_offset can be provided to EbStandardMiscText")
        if not maximum_size:
            raise ValueError("maximum_size must be provided")

        self.pointer = pointer
        self.default_offset = default_offset
        if not null_terminated:
            self.table_entry = EbStandardTextTableEntry.create(maximum_size)
        else:
            self.table_entry = EbStandardNullTerminatedTextTableEntry.create(maximum_size)

    def from_block(self, block):
        if self.pointer:
            loc = self.pointer.read(block)
        else:
            loc = self.default_offset

        return self.table_entry.from_block(block, loc)

    def to_block(self, block, value):
        if self.pointer:
            loc = block.allocate(size=self.table_entry.size)
            self.pointer.write(block, to_snes_address(loc))
        else:
            loc = self.default_offset

        self.table_entry.to_block(block, loc, value)

MISC_TEXT = {
    "Starting Text": {
        "Start New Game": EbMiscTextString(default_offset=0x004c060, maximum_size=14),
        "Text Speed": EbMiscTextString(default_offset=0x04c074, maximum_size=11),
        "Text Speed Fast": EbMiscTextString(default_offset=0x04c07f, maximum_size=6),
        "Text Speed Medium": EbMiscTextString(default_offset=0x04c086, maximum_size=6),
        "Text Speed Slow": EbMiscTextString(default_offset=0x04c08d, maximum_size=6),
        "Continue": EbMiscTextString(pointer=EbMiscTextAsmPointer(0x1F08C), maximum_size=25, null_terminated=True),
        "Copy": EbMiscTextString(pointer=EbMiscTextAsmPointer(0x1F0C5), maximum_size=25, null_terminated=True),
        "Delete": EbMiscTextString(pointer=EbMiscTextAsmPointer(0x1F102), maximum_size=25, null_terminated=True),
        "Set Up": EbMiscTextString(pointer=EbMiscTextAsmPointer(0x1F120), maximum_size=25, null_terminated=True),
        "Copy to where?": EbMiscTextString(default_offset=0x04c0b0, maximum_size=14),
        "Confirm Delete": EbMiscTextString(default_offset=0x04c0be, maximum_size=32),
        "Confirm Delete No": EbMiscTextString(default_offset=0x04c0de, maximum_size=2),
        "Confirm Delete Yes": EbMiscTextString(default_offset=0x04c0e1, maximum_size=3),
        "Select Speed": EbMiscTextString(default_offset=0x04c0e5, maximum_size=25),
        "Select Sound": EbMiscTextString(default_offset=0x04c0fe, maximum_size=28),
        "Select Sound Stereo": EbMiscTextString(default_offset=0x04c11a, maximum_size=6),
        "Select Sound Mono": EbMiscTextString(default_offset=0x04c121, maximum_size=6),
        "Select Style": EbMiscTextString(default_offset=0x04c128, maximum_size=37),
        "Ask Name 1": EbMiscTextString(default_offset=0x04c194, maximum_size=40),
        "Ask Name 2": EbMiscTextString(default_offset=0x04c1bc, maximum_size=40),
        "Ask Name 3": EbMiscTextString(default_offset=0x04c1e4, maximum_size=40),
        "Ask Name 4": EbMiscTextString(default_offset=0x04c20c, maximum_size=40),
        "Ask Name Pet": EbMiscTextString(default_offset=0x04c234, maximum_size=40),
        "Ask Name Food": EbMiscTextString(default_offset=0x04c25c, maximum_size=40),
        "Ask Name PSI": EbMiscTextString(default_offset=0x04c284, maximum_size=40),
        "Confirm Food": EbMiscTextString(default_offset=0x04c2ac, maximum_size=14),
        "Confirm PSI": EbMiscTextString(default_offset=0x04c2ba, maximum_size=14),
        "Confirm All": EbMiscTextString(default_offset=0x04c2c8, maximum_size=13),
        "Confirm All Yes": EbMiscTextString(default_offset=0x04c2d5, maximum_size=3),
        "Confirm All No": EbMiscTextString(default_offset=0x04c2d9, maximum_size=4)
    },
    "Ailments": {
        "Ailment 01": EbMiscTextString(default_offset=0x045b70, maximum_size=16),
        "Ailment 02": EbMiscTextString(default_offset=0x045b80, maximum_size=16),
        "Ailment 03": EbMiscTextString(default_offset=0x045b90, maximum_size=16),
        "Ailment 04": EbMiscTextString(default_offset=0x045ba0, maximum_size=16),
        "Ailment 05": EbMiscTextString(default_offset=0x045bb0, maximum_size=16),
        "Ailment 06": EbMiscTextString(default_offset=0x045bc0, maximum_size=16),
        "Ailment 07": EbMiscTextString(default_offset=0x045bd0, maximum_size=16),
        "Ailment 08": EbMiscTextString(default_offset=0x045be0, maximum_size=16),
        "Ailment 09": EbMiscTextString(default_offset=0x045bf0, maximum_size=16),
        "Ailment 10": EbMiscTextString(default_offset=0x045c00, maximum_size=16)
    },
    "Battle Menu": {
        "Bash": EbMiscTextString(default_offset=0x049fe1, maximum_size=16),
        "Goods": EbMiscTextString(default_offset=0x049ff1, maximum_size=16),
        "Auto Fight": EbMiscTextString(default_offset=0x04a001, maximum_size=16),
        "PSI": EbMiscTextString(default_offset=0x04a011, maximum_size=16),
        "Defend": EbMiscTextString(default_offset=0x04a021, maximum_size=16),
        "Pray": EbMiscTextString(default_offset=0x04a031, maximum_size=16),
        "Shoot": EbMiscTextString(default_offset=0x04a041, maximum_size=16),
        "Spy": EbMiscTextString(default_offset=0x04a051, maximum_size=16),
        "Run Away": EbMiscTextString(default_offset=0x04a061, maximum_size=16),
        "Mirror": EbMiscTextString(default_offset=0x04a071, maximum_size=16),
        "Do Nothing": EbMiscTextString(default_offset=0x04a081, maximum_size=11)  # New in CoilSnake 2.0
    },
    "Out of Battle Menu": {
        "Talk to": EbMiscTextString(default_offset=0x2fa37a, maximum_size=9),
        "Goods": EbMiscTextString(default_offset=0x2fa384, maximum_size=9),
        "PSI": EbMiscTextString(default_offset=0x2fa38e, maximum_size=9),
        "Equip": EbMiscTextString(default_offset=0x2fa398, maximum_size=9),
        "Check": EbMiscTextString(default_offset=0x2fa3a2, maximum_size=9),
        "Status": EbMiscTextString(default_offset=0x2fa3ac, maximum_size=9)
    },
    "Status Window": {
        "Level": EbMiscTextString(default_offset=0x2fa3ba, maximum_size=6, null_terminated=True),
        "Hit Points": EbMiscTextString(default_offset=0x2fa3c4, maximum_size=11, null_terminated=True),
        "Psychic Points": EbMiscTextString(default_offset=0x2fa3d3, maximum_size=15, null_terminated=True),
        "Experience Points": EbMiscTextString(default_offset=0x2fa3e6, maximum_size=18, null_terminated=True),
        "Exp. for next level": EbMiscTextString(default_offset=0x2fa3fc, maximum_size=20, null_terminated=True),
        "Offense": EbMiscTextString(default_offset=0x2fa414, maximum_size=8, null_terminated=True),
        "Defense": EbMiscTextString(default_offset=0x2fa420, maximum_size=8, null_terminated=True),
        "Speed": EbMiscTextString(default_offset=0x2fa42c, maximum_size=6, null_terminated=True),
        "Guts": EbMiscTextString(default_offset=0x2fa436, maximum_size=5, null_terminated=True),
        "Vitality": EbMiscTextString(default_offset=0x2fa43f, maximum_size=9, null_terminated=True),
        "IQ": EbMiscTextString(default_offset=0x2fa44c, maximum_size=3, null_terminated=True),
        "Luck": EbMiscTextString(default_offset=0x2fa453, maximum_size=5, null_terminated=True),
        "PSI Prompt": EbMiscTextString(default_offset=0x045b4d, maximum_size=35, null_terminated=True)
    },
    "Other": {
        "Player Name Prompt": EbMiscTextString(default_offset=0x03fb2b, maximum_size=36),
        "Lumine Hall Text": EbMiscTextString(default_offset=0x048037, maximum_size=213)
    },
    "PSI Types": {
        "Offense": EbMiscTextString(default_offset=0x03f090, maximum_size=7),
        "Recover": EbMiscTextString(default_offset=0x03f098, maximum_size=7),
        "Assist": EbMiscTextString(default_offset=0x03f0a0, maximum_size=7),
        "Other": EbMiscTextString(default_offset=0x03f0a8, maximum_size=7)
    },
    "PSI Menu": {
        "PP Cost": EbMiscTextString(default_offset=0x03f11c, maximum_size=7),
        "To enemy": EbMiscTextString(default_offset=0x03f124, maximum_size=19),
        "To one enemy": EbMiscTextString(default_offset=0x03f138, maximum_size=19),
        "To one enemy 2": EbMiscTextString(default_offset=0x03f14c, maximum_size=19),
        "To row of foes": EbMiscTextString(default_offset=0x03f160, maximum_size=19),
        "To all enemies": EbMiscTextString(default_offset=0x03f174, maximum_size=19),
        "himself": EbMiscTextString(default_offset=0x03f188, maximum_size=19),
        "To one of us": EbMiscTextString(default_offset=0x03f19c, maximum_size=19),
        "To one of us 2": EbMiscTextString(default_offset=0x03f1b0, maximum_size=19),
        "To all of us": EbMiscTextString(default_offset=0x03f1c4, maximum_size=19),
        "To all of us 2": EbMiscTextString(default_offset=0x03f1d8, maximum_size=19),
        "Row To": EbMiscTextString(default_offset=0x0454f2, maximum_size=3),
        "Row Front": EbMiscTextString(default_offset=0x0454f5, maximum_size=13),
        "Row Back": EbMiscTextString(default_offset=0x45502, maximum_size=15)
    },
    "Equip Menu": {
        "Offense": EbMiscTextString(default_offset=0x045c1c, maximum_size=7),
        "Defense": EbMiscTextString(default_offset=0x045c24, maximum_size=7),
        "Weapon": EbMiscTextString(default_offset=0x045c2c, maximum_size=10),
        "Body": EbMiscTextString(default_offset=0x045c37, maximum_size=10),
        "Arms": EbMiscTextString(default_offset=0x045c42, maximum_size=10),
        "Other": EbMiscTextString(default_offset=0x045c4d, maximum_size=10),
        "Weapon Window Title": EbMiscTextString(default_offset=0x045c58, maximum_size=7),
        "Body Window Title": EbMiscTextString(default_offset=0x045c60, maximum_size=7),
        "Arms Window Title": EbMiscTextString(default_offset=0x045c68, maximum_size=7),
        "Other Window Title": EbMiscTextString(default_offset=0x045c70, maximum_size=7),
        "No Equip": EbMiscTextString(default_offset=0x045c78, maximum_size=9),
        "Unequip": EbMiscTextString(default_offset=0x045c82, maximum_size=4),
        "To": EbMiscTextString(default_offset=0x045c87, maximum_size=2)
    },
    "Item Menu": {
        "Use": EbMiscTextString(default_offset=0x043550, maximum_size=5),
        "Give": EbMiscTextString(default_offset=0x043556, maximum_size=5),
        "Drop": EbMiscTextString(default_offset=0x04355c, maximum_size=5),
        "Help": EbMiscTextString(default_offset=0x043562, maximum_size=5)
    },
    "Menu Action Targets": {
        "Who": EbMiscTextString(default_offset=0x045963, maximum_size=9),
        "Which": EbMiscTextString(default_offset=0x04596d, maximum_size=9),
        "Where": EbMiscTextString(default_offset=0x045977, maximum_size=9),
        "Whom": EbMiscTextString(default_offset=0x045981, maximum_size=9),
        "Where 2": EbMiscTextString(default_offset=0x04598b, maximum_size=9)
    },
    "Window Titles": {
        "Escargo Express Window Title": EbMiscTextString(default_offset=0x045c10, maximum_size=12),
        "Phone Window Title": EbMiscTextString(default_offset=0x045995, maximum_size=4)
    }
}


class MiscTextModule(EbModule):
    NAME = "Miscellaneous Text"

    def __init__(self):
        super(MiscTextModule, self).__init__()
        self.data = dict()

    def read_from_rom(self, rom):
        for category_name, category in MISC_TEXT.iteritems():
            category_data = dict()
            for item_name, item in category.iteritems():
                category_data[item_name] = item.from_block(rom)
            self.data[category_name] = category_data

    def write_to_rom(self, rom):
        for category_name, category in MISC_TEXT.iteritems():
            for item_name, item in category.iteritems():
                item.to_block(rom, self.data[category_name][item_name])

    def read_from_project(self, resource_open):
        with resource_open("text_misc", "yml") as f:
            self.data = yml_load(f)

    def write_to_project(self, resource_open):
        with resource_open("text_misc", "yml") as f:
            yml_dump(self.data, f, default_flow_style=False)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version == 4:
            self.read_from_project(resource_open_r)

            item = MISC_TEXT["Battle Menu"]["Do Nothing"]
            self.data["Battle Menu"]["Do Nothing"] = item.from_block(rom)

            self.write_to_project(resource_open_w)

            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        elif old_version <= 2:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
            self.upgrade_project(3, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)