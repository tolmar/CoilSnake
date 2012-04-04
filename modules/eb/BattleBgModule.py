import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import EbCompressedData, DataBlock
from CompressedGraphicsModule import EbArrangement, EbTileGraphics, EbPalettes
from modules.Progress import updateProgress

from PIL import Image

class BattleBgModule(EbModule.EbModule):
    _name = "Battle Backgrounds"
    _ASMPTRS_GFX = [0x2d1ba, 0x2d4dc, 0x2d8c3, 0x4a3ba]
    _ASMPTRS_ARR = [0x2d2c1, 0x2d537, 0x2d91f, 0x4a416]
    _ASMPTRS_PAL = [0x2d3bb, 0x2d61b, 0x2d7e8, 0x2d9e8, 0x4a4d0]
    def __init__(self):
        self._bbgGfxPtrTbl = EbTable(0xcad7a1)
        self._bbgArrPtrTbl = EbTable(0xcad93d)
        self._bbgPalPtrTbl = EbTable(0xcadad9)
        self._bbgGroupTbl = EbTable(0xCBD89A)
        self._bbgScrollTbl = EbTable(0xCAF258)
        self._bbgDistorTbl = EbTable(0xCAF708)
        self._bbgTbl = EbTable(0xcadca1)
    def free(self):
        del(self._bbgGfxPtrTbl)
        del(self._bbgArrPtrTbl)
        del(self._bbgPalPtrTbl)
        del(self._bbgGroupTbl)
        del(self._bbgTbl)

        del(self._bbgGfxArrs)
        del(self._bbgPals)
    def readFromRom(self, rom):
        self._bbgTbl.readFromRom(rom)
        pct = 50.0/(6+self._bbgTbl.height())
        self._bbgGfxPtrTbl.readFromRom(rom,
                EbModule.toRegAddr(EbModule.readAsmPointer(rom,
                    self._ASMPTRS_GFX[0])))
        updateProgress(pct)
        self._bbgArrPtrTbl.readFromRom(rom,
                EbModule.toRegAddr(EbModule.readAsmPointer(rom, 
                    self._ASMPTRS_ARR[0])))
        updateProgress(pct)
        self._bbgPalPtrTbl.readFromRom(rom,
                EbModule.toRegAddr(EbModule.readAsmPointer(rom, 
                    self._ASMPTRS_PAL[0])))
        updateProgress(pct)

        self._bbgGfxArrs = [ None for i in range(self._bbgGfxPtrTbl.height()) ]
        self._bbgPals = [ None for i in range(self._bbgPalPtrTbl.height()) ]
        self._bbgGroupTbl.readFromRom(rom)
        updateProgress(pct)
        self._bbgScrollTbl.readFromRom(rom)
        updateProgress(pct)
        self._bbgDistorTbl.readFromRom(rom)
        updateProgress(pct)
        for i in range(self._bbgTbl.height()):
            gfxNum = self._bbgTbl[i,0].val()
            colorDepth = self._bbgTbl[i,2].val()
            if (self._bbgGfxArrs[gfxNum] == None):
                tgb = EbCompressedData()
                tgb.readFromRom(rom,
                        EbModule.toRegAddr(self._bbgGfxPtrTbl[gfxNum,0].val()))
                ab = EbCompressedData()
                ab.readFromRom(rom,
                        EbModule.toRegAddr(self._bbgArrPtrTbl[gfxNum,0].val()))
                # Max size used in rom: 421 (2bpp) 442 (4bpp)
                tg = EbTileGraphics(512, 8, colorDepth)
                tg.readFromBlock(tgb)
                a = EbArrangement(32, 32)
                a.readFromBlock(ab)
                del(tgb)
                del(ab)
                self._bbgGfxArrs[gfxNum] = (tg, a)
            palNum = self._bbgTbl[i,1].val()
            if (self._bbgPals[palNum] == None):
                pb = DataBlock(32)
                pb.readFromRom(rom,
                        EbModule.toRegAddr(self._bbgPalPtrTbl[palNum,0].val()))
                p = EbPalettes(1, 16)
                p.readFromBlock(pb)
                del(pb)
                self._bbgPals[palNum] = p
            updateProgress(pct)
    def writeToProject(self, resourceOpener):
        pct = 50.0/(4+self._bbgTbl.height())
        self._bbgTbl.writeToProject(resourceOpener, hiddenColumns=[0,1])
        updateProgress(pct)
        self._bbgGroupTbl.writeToProject(resourceOpener)
        updateProgress(pct)
        self._bbgScrollTbl.writeToProject(resourceOpener)
        updateProgress(pct)
        self._bbgDistorTbl.writeToProject(resourceOpener)
        updateProgress(pct)
        # Export BGs by table entry
        for i in range(self._bbgTbl.height()):
            (tg, a) = self._bbgGfxArrs[self._bbgTbl[i,0].val()]
            pal = self._bbgTbl[i,1].val()
            img = a.toImage(tg, self._bbgPals[pal])
            imgFile = resourceOpener('BattleBGs/' + str(i).zfill(3), 'png')
            img.save(imgFile, 'png')
            imgFile.close()
            del(img)
            updateProgress(pct)
    def readFromProject(self, resourceOpener):
        self._bbgTbl.readFromProject(resourceOpener)
        pct = 50.0/(3+self._bbgTbl.height())
        self._bbgGroupTbl.readFromProject(resourceOpener)
        updateProgress(pct)
        self._bbgScrollTbl.readFromProject(resourceOpener)
        updateProgress(pct)
        self._bbgDistorTbl.readFromProject(resourceOpener)
        updateProgress(pct)
        self._bbgGfxArrs = []
        self._bbgPals = []
        for i in range(self._bbgTbl.height()):
            img = Image.open(
                    resourceOpener('BattleBGs/' + str(i).zfill(3), 'png'))

            np = EbPalettes(1, 16)
            colorDepth = self._bbgTbl[i,2].val()
            # Max size used in rom: 421 (2bpp) 442 (4bpp)
            ntg = EbTileGraphics(512, 8, colorDepth)
            na = EbArrangement(32, 32)
            na.readFromImage(img, np, ntg)
            j=0
            for (tg, a) in self._bbgGfxArrs:
                if (tg == ntg) and (a == na):
                    self._bbgTbl[i,0].setVal(j)
                    break
                j += 1
            else:
                self._bbgGfxArrs.append((ntg, na))
                self._bbgTbl[i,0].setVal(j)
            j=0
            for p in self._bbgPals:
                if (p == np):
                    self._bbgTbl[i,1].setVal(j)
                    break
                j += 1
            else:
                self._bbgPals.append((np))
                self._bbgTbl[i,1].setVal(j)
            updateProgress(pct)
    def freeRanges(self):
        return [(0xa0000,0xadca0), (0xb0000, 0xbd899)]
    def writeToRom(self, rom):
        self._bbgGfxPtrTbl.clear(len(self._bbgGfxArrs))
        self._bbgArrPtrTbl.clear(len(self._bbgGfxArrs))
        self._bbgPalPtrTbl.clear(len(self._bbgPals))

        # Write gfx+arrs
        i = 0
        pct = (50.0/3)/len(self._bbgGfxArrs)
        for (tg, a) in self._bbgGfxArrs:
            tgb = EbCompressedData()
            tgb.clear(tg.sizeBlock())
            tg.writeToBlock(tgb)
            ab = EbCompressedData()
            ab.clear(a.sizeBlock())
            a.writeToBlock(ab)
            self._bbgGfxPtrTbl[i,0].setVal(EbModule.toSnesAddr(
                    tgb.writeToFree(rom)))
            self._bbgArrPtrTbl[i,0].setVal(EbModule.toSnesAddr(
                    ab.writeToFree(rom)))
            del(tgb)
            del(ab)
            i += 1
            updateProgress(pct)
        EbModule.writeAsmPointers(rom, self._ASMPTRS_GFX,
                EbModule.toSnesAddr(self._bbgGfxPtrTbl.writeToFree(rom)))
        EbModule.writeAsmPointers(rom, self._ASMPTRS_ARR,
                EbModule.toSnesAddr(self._bbgArrPtrTbl.writeToFree(rom)))

        # Write pals
        i = 0
        pct = (50.0/3)/len(self._bbgPals)
        for p in self._bbgPals:
            pb = DataBlock(32)
            pb.clear(p.sizeBlock())
            p.writeToBlock(pb)
            self._bbgPalPtrTbl[i,0].setVal(EbModule.toSnesAddr(
                    pb.writeToFree(rom)))
            del(pb)
            i += 1
            updateProgress(pct)
        EbModule.writeAsmPointers(rom, self._ASMPTRS_PAL,
                EbModule.toSnesAddr(self._bbgPalPtrTbl.writeToFree(rom)))

        # Write the data table
        pct = (50.0/3)/4
        self._bbgTbl.writeToRom(rom)
        updateProgress(pct)
        self._bbgGroupTbl.writeToRom(rom)
        updateProgress(pct)
        self._bbgScrollTbl.writeToRom(rom)
        updateProgress(pct)
        self._bbgDistorTbl.writeToRom(rom)
        updateProgress(pct)
