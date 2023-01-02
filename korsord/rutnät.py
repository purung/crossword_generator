from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field, astuple
from pathlib import Path
from importlib import resources

from rich.live import Live
from rich.traceback import install
from rich.progress import track
from rich.table import Table
from rich import box, console, panel
from rich import print
from random import choice, random, randrange, sample
from collections import deque, defaultdict
from itertools import takewhile, cycle
from operator import attrgetter, itemgetter
from statistics import mean
from parse import search
import string
import datetime
from functools import lru_cache
import re

install(show_locals=True)


class Ruta(str, Enum):
    TOM = "□"
    BLOCK = "■"

    def __repr__(self) -> str:
        return str(self.value)

    def __str__(self):
        return self.value


@dataclass(unsafe_hash=True, order=False, eq=False)
class Läge:
    __slots__ = ["x", "y", "z"]
    x: int
    y: int
    z: int

    def __eq__(self, lg: Läge):
        return self.x == lg.x and self.y == lg.y

    def __lt__(self, lg: Läge):
        return self.x * self.y < lg.x * lg.y 
    
    def __sub__(self, steg: int):
        if self.z:
            return Läge(max(0, self.x - steg), self.y, self.z)
        else:
            return Läge(self.x, max(0, self.y - 1), self.z)

    def __add__(self, steg: int):
        if self.z:
            return Läge(self.x + steg, self.y, self.z)
        else:
            return Läge(self.x, self.y + steg, self.z)

    @property
    def kant(self):
        return self.z and self.x == 0 or not self.z and self.y == 0

    def slice(self):
        return slice(self.x, self.y)
    
    def lägeskänslig(self, lg: Läge):
        xy = self == lg
        z = self.z == lg.z
        return xy and z  


@dataclass(unsafe_hash=True)
class Ord:
    __slots__ = ["ord", "läge", "special", "pre", "post"]
    ord: str
    läge: Läge
    special: bool
    pre: bool
    post: bool

    def __post_init__(self):
        self.ord = self.ord.strip(f"\n{Ruta.BLOCK} ")

    def __eq__(self, rd: Ord):
        return self.ord == rd.ord

    def __len__(self):
        return len(str(self))

    def __str__(self):
        return f"{Ruta.BLOCK if self.pre else ''}{self.ord}{Ruta.BLOCK if self.post else ''}"

    @lru_cache(maxsize=3000)
    def __contains__(self, sub: str):
        return sub in str(self)

    def __next__(self):
        return next(self.__iter__())

    def __iter__(self):
        return iter(str(self))

    def __getitem__(self, slice: slice):
        return str(self)[slice]

    @property
    def kort(self):
        return len(self.ord) < 3

    @property
    def vertikalt(self) -> bool:
        if self.läge:
            return bool(self.läge.z)

    @property
    def horisontellt(self) -> bool:
        if self.vertikalt is not None:
            return not self.vertikalt

    def skiva(self) -> slice:
        if not self.läge:
            raise ValueError
        if self.horisontellt:
            return slice(self.läge.y, self.läge.y + len(self))
        return slice(self.läge.x, self.läge.x + (len(self)))

    @property
    def poäng(self):
        import random 
        seed = random.random()
        poäng = seed * len(self) if not self.special else len(self)
        return poäng ** 3 if self.special else poäng

    def positionera(self, läge: Läge):
        self.läge = läge
        return self

    def blockera(self, pre=None, post=None):
        if pre is not None:
            self.pre = pre
        if post is not None:
            self.post = post
        return self

    def stäng(self, post=False):
        if not self.läge.kant and not self.pre:
            self.positionera(self.läge - 1)
            self.pre = True
        if post and not self.post:
            self.post = True 

    def reset(self):
        self.läge = None
        self.blockera(pre=False, post=False)
        return self
    
    def lägeskänslig(self, rd: Ord) -> bool:
        return self == rd and self.läge.lägeskänslig(rd.läge)

    def förekomst(self, bks: str) -> list[int]:
        return förekomst(str(self), bks)

@lru_cache(maxsize=1000000)
def förekomst(rd: str, sub: str) -> list[int]:
    if rd == sub:
        return []
    st = [m.start() for m in re.finditer(sub, rd)]
    return st

@dataclass(unsafe_hash=True)
class Ordlista:
    ord: list[Ord] = field(default_factory=list, compare=False)
    index: dict[str, set[Ord]] = field(compare=False, repr=False, default=None)
    omöjliga: list[str] = field(default_factory=list, compare=False)

    @lru_cache(maxsize=100000)
    def __contains__(self, ord: Ord) -> bool:
        """Ordet finns i ordlistan"""
        return ord in self.ord

    def ladda(self):
        with resources.open_text("korsord", "feff.txt", "utf-8") as specialfil:
            self.ord += [Ord(o.upper(), None, True, False, False) for o in specialfil.readlines() if o]
        with resources.open_text("korsord", "words.txt", "utf-8") as vanligfil:
            self.ord += [Ord(o, None, False, False, False) for o in vanligfil.readlines() if o]
        self.ord = sorted(self.ord, key=attrgetter("poäng"), reverse=True)
        self.index = defaultdict(set)
        return self

    def cache(self):
        bokstäver = (string.ascii_letters + "åäöé").upper()
        for bks in track(bokstäver, description="Bygger cachce..."):
            for rd in self.ord:
                if rd.förekomst(bks):
                    self.index[bks].add(rd)
        

    def __enter__(self):
        self.ladda()
        self.cache()
        return self

    def __exit__(self, *args):
        # with Path("./omöjliga.txt").open(mode="w", encoding="utf-8") as omöjligfil:
        #    spara = [o for o in sorted(self.omöjliga, key=len) if len(o) < 5]
        #   for omöjlig in spara:
        #        omöjligfil.write(omöjlig + "\n")
        pass

    def __getitem__(self, ord: str) -> Ord:
        return next(o for o in self.ord if o == ord)

    def __repr__(self) -> str:
        return f"<Ordlista med {len(self.ord)} ord>"

    def __iter__(self):
        return iter(self.ord)

    def __next__(self):
        return next(iter(self))


    @lru_cache(maxsize=50000)
    def omöjligt(self, sub: str):
        return sub in self.omöjliga

    def mellanrum(self, pre: str, post: str, fria: int) -> list[Ord]:
        del_1 = self.index[pre]
        del_2 = self.index[post]
        med_i = del_1.intersection(del_2)
        filtrerat = [rd for rd in med_i if fyller_mellanrum(pre, post, fria, rd.ord)]
        return sorted(filtrerat, key=attrgetter("poäng"), reverse=True)

    def kompatibla(self, sub: str) -> list[Ord]:
        if not isinstance(sub, str):
            raise ValueError
        if self.omöjligt(sub):
            return []
        if cache := self.index[sub]:
            return sorted(list(cache), key=attrgetter("poäng"), reverse=True)
        bitar = set(self.index[sub[0]])
        if not bitar:
            return []
        for bks in sub[1:]:
            bitar = bitar.intersection(self.index[bks])
            if not bitar:
                return []
        komp = [o for o in bitar if o.förekomst(sub)]
        self.index[sub] = set(komp)
        if not komp and len(sub) < 5:
            self.omöjliga.append(sub)
        return sorted(komp, key=attrgetter("poäng"), reverse=True)

@lru_cache(maxsize=200000)
def ord_i_lista(rad: tuple) -> list[str]:
    split_på_tomma = "".join(rad).split(Ruta.TOM)
    if not any(split_på_tomma):
        return []
    split_på_block = [
        "".join(sb)
        for sek in split_på_tomma
        for sb in sek.split(Ruta.BLOCK.value)
        if sek
    ]
    rensad = [o for o in split_på_block if o and 1 < len(o)]
    return rensad

@lru_cache(maxsize=1000000)
def fyller_mellanrum(pre: str, post: str, fria: int, rd: str):
    tomma = "{{w:.{antal}}}".format(antal=fria)
    mtch = search(pre + tomma + post, rd)
    return mtch is not None

@dataclass(unsafe_hash=True)
class Korsord:
    höjd: int
    bredd: int
    ordlista: Ordlista = field(default=None, repr=False, compare=False)
    konsol: console.Console = field(default_factory=console.Console, compare=False)
    ord: list[Ord] = field(default_factory=list, repr=False, compare=False)
    aparta: dict[Ord, list[Ord]] = field(default_factory=dict, repr=False, compare=False)
    kors: dict[Läge, Kors] = field(default_factory=dict, repr=False, compare=False)

    def __enter__(self):
        lägen = [
            Läge(x, y, 0) for x, rad in enumerate(self.rader()) for y, ltr in enumerate(rad)
        ]
        self.kors.update(
            {l: Kors(l, self, Riktning.INGA, {}) for l in track(lägen, description="Skapar kors...")}
        )
        self.starta()
        return self

    def __exit__(self, *args):
        with Path("./sparade.txt").open(mode="a", encoding="utf-8") as bank:
            bank.write(str(self))
            bank.write(f"\nPoäng: {self.poängräkning()}\n\n")

    def rendera(self) -> list[str]:
        return [" ".join(rad) for rad in self.rader()]

    def __str__(self) -> str:
        return "\n".join(self.rendera())

    @lru_cache
    def __rutnät(self, ord: tuple[Ord]) -> list[list[str]]:
        """Tolka alla ord till rutnätet"""
        nät = []
        for r in range(self.höjd):
            rad = [Ruta.TOM for k in range(self.bredd)]
            ord = [o for o in self.ord if o.horisontellt and o.läge.x == r]
            for o in ord:
                rad[o.skiva()] = list(o)
            nät.append(rad)
        for y, k in enumerate(zip(*nät)):
            kol = list(k)
            ord = [o for o in self.ord if o.vertikalt and o.läge.y == y]
            if not ord:
                continue
            for o in ord:
                sk = o.skiva()
                kol[sk] = list(o)
                kol = kol[0 : self.höjd]
            for x, bks in enumerate(kol):
                nät[x][y] = bks
        return nät

    def __getitem__(self, skiva: slice) -> str:
        return self.kors[Läge(skiva.start, skiva.stop, 0)]

    def __contains__(self, rd: Ord):
        if isinstance(rd, Ord):
            return rd in self.ord
        elif isinstance(rd, str):
            return Ord(o, None, True, False, False) in self.ord 

    def __rich_console__(self, console, options):
        stil = {Ruta.BLOCK.value: "[dark_blue]{} ", Ruta.TOM: "[dark_green]{} "}
        rutnät = []
        for rad in self.rader():
            cols = [stil.get(col, "[b][yellow]{} [/b]").format(col)
                    for col in rad]
            rutnät.append(" ".join(cols))
        yield panel.Panel("\n".join(rutnät), box=box.DOUBLE_EDGE, expand=False)

    
    def rader(self) -> list[list[str]]:
        """Skapa rader"""
        return self.__rutnät(tuple(self.ord))
    
    def kolumner(self) -> list[list[str]]:
        """Rotera rader till kolumner"""
        return list(zip(*self.rader()))

    def hitta(self, bks: str) -> list[tuple[int, int]]:
        """Se alla koordinater för en viss bokstav"""
        if not len(bks) == 1:
            return []
        bks = bks.upper()
        return [
            Läge(x, y, 0)
            for x, rad in enumerate(self.rader())
            for y, ltr in enumerate(rad)
            if bks == ltr
        ]


    def horisontella_ord(self) -> list[Ord]:
        """Alla ord som bildas längsmed rader"""

        def lg(ix, o):
            lg = Läge(ix, max(0, "".join(self.rad(ix)).find(o)), 0)
            if lg is None:
                raise ValueError
            return lg 

        rds = [
            Ord(o, lg(ix, o), False, False, False)
            for ix, rad in enumerate(self.rader())
            for o in ord_i_lista(tuple(rad))
            if 1 < len(o)
        ]
        
        if any(rd.läge is None for rd in rds):
            raise ValueError
        return rds

    def vertikala_ord(self) -> list[Ord]:
        """Alla ord som bildas längsmed kolumner"""

        def lg(ix, o):
            lg = Läge(max(0, "".join(self.kolumn(ix)).find(o)), ix, 1)
            if lg is None:
                raise ValueError
            return lg

        rds = [
            Ord(o, lg(ix, o), False, False, False)
            for ix, kol in enumerate(self.kolumner())
            for o in ord_i_lista(tuple(kol))
            if 1 < len(o)
        ]
        if any(rd.läge is None for rd in rds):
            raise ValueError
        return rds

    def alla_ord(self) -> list[Ord]:
        """Alla ord som bildas i korsordet"""
        alla = [*self.horisontella_ord(), *self.vertikala_ord()]
        return alla

    def rad(self, ix: int) -> list[str]:
        return self.rader()[ix]

    def kolumn(self, ix: int) -> list[str]:
        return self.kolumner()[ix]

    
    def nya_ord(self, ref: list[Ord]):
        ord_just_nu = self.alla_ord()
        aparta = [ap for sk in self.aparta.values() for ap in sk]
        if any(ap.läge is None for ap in aparta):
            raise ValueError("Hur hände det att något blev None")
            # något med ord som ersätts av längre ord
            # något med att de plötsligt får läge None
        fällda = []
        for rd in ord_just_nu:
            sedd = any(obs.lägeskänslig(rd) for obs in ref)
            upplockad = any(obs.lägeskänslig(rd) for obs in aparta)
            if sedd or upplockad:
                continue
            else:
                fällda.append(rd)
        if any(ap.läge is None for ap in fällda):
            raise ValueError("Hur hände det att något blev None")
        return sorted(fällda, key=len, reverse=True)

    def sätt(self, rd: Ord):
        self.konsol.log(f"Prövar att lägga till [dark_sea_green4]{rd.ord}...")
        cnt = self.alla_ord()
        self.ord.append(rd)
        if fällda := [o for o in self.nya_ord(cnt) if o != rd]:
            self.konsol.log(f"[orange3]{rd.ord} skapade {len(fällda)} biverkningar...")
            self.aparta[rd] = fällda
        return fällda

    def stubbar(self):
        for stubb in sorted([o for o in self.ord if 1 < len(o.ord) if not o.pre or not o.post], key=len):
            kompatibla = self.ordlista.kompatibla(stubb.ord)
            flagg = False
            for kmp in kompatibla:
                if stubb.läge.z:
                    if next((rd.läge.x == stubb.läge.x for rd in self.ord), False):
                        flagg = True
                        break
                else:
                    if next((rd.läge.y == stubb.läge.y for rd in self.ord), False):
                        flagg = True
                        break
            if flagg:
                continue
            kors = self[stubb.läge.slice()]
            if not kompatibla:
                stubb.stäng(post=True)
            if not (kors.tömd is Riktning(stubb.läge.z) or kors.tömd is Riktning.BÅDA):
                self.konsol.log(f"[dark_sea_green4]Fortsätter på {stubb.ord}...")
                yield from kors.möjligheter(kompatibla, överskrift=True, enbart=Riktning(stubb.läge.z))
            else:
                slut = stubb.läge + len(stubb) + 1
                finns = next((krs for krs in self.kors.values() if krs.läge == slut), None)
                if finns and finns.origo is Ruta.TOM:
                    stubb.stäng(post=True)
                else:
                    stubb.stäng()

    def mellanrum(self):
        for krs in self.kors.values():
            if krs.tom or krs.låst or krs.gåta:
                continue
            if (krs.tömd is Riktning.INGA or krs.tömd is Riktning.VERTIKALT) and krs.mellanrum_e is not None:
                kompatibla = self.ordlista.mellanrum(*krs.mellanrum_e)
                self.konsol.log(f"[dark_sea_green4]Prövar att fylla i {krs!r}...")
                yield from krs.möjligheter(kompatibla, enbart=Riktning.HORISONTELLT, töm=False)
            if (krs.tömd is Riktning.INGA or krs.tömd is Riktning.HORISONTELLT) and krs.mellanrum_s is not None:
                kompatibla = self.ordlista.mellanrum(*krs.mellanrum_s)
                self.konsol.log(f"[dark_sea_green4]Prövar att fylla i {krs!r}...")
                yield from krs.möjligheter(kompatibla, enbart=Riktning.VERTIKALT, töm=False)

    def generera_kors(self):
        import random
        svåra_hakningar = "ZXCFHBYQUWJÅÄÖ"
        sortering = dict(zip(svåra_hakningar, range(len(svåra_hakningar))))
        def sortera(kors):
            return sortering.get(kors.origo, random.randrange(0, 20))

        while True:
            try:
                kors = sorted([k for k in self.kors.values() if not (k.låst or k.tom or k.kant or k.tömd is Riktning.BÅDA)])
                random.shuffle(kors)
                # friheter 
                yield from (a for a in sorted(kors, key=sortera, reverse=True)[:10])
                hori = (a for a in sorted(kors, key=attrgetter("friheter_horisontellt"), reverse=True))
                verti = (a for a in sorted(kors, key=attrgetter("friheter_vertikalt"), reverse=True))
                for ax in zip(hori, verti):
                    yield choice(ax)

                # svåra bokstäver

            except Fortare:
                self.konsol.log(f"[dark_sea_green4]Startar om korshårsloopen...")
                continue

    def möjligheter(self):
        import random
        korshår = self.generera_kors()
        seed = random.random()
        while True:
            try:
                yield from self.stubbar()
                if 0.3 >= seed < 0.55:
                    yield from self.mellanrum()
                for kors in korshår:
                    if kors.gåta:
                        kompatibla = self.ordlista.ord
                    else:
                        kompatibla = self.ordlista.kompatibla(kors.origo)
                    yield from kors.möjligheter(kompatibla, gräns=25)
                else:
                    break
            except Fortare:
                korshår.throw(Fortare)
                continue

    def hantera_aparta(self, rd: Ord = None, aparta: list[Ord] = None):
        """Rekursiv funktion för att lösa ogiltiga ord"""
        nya = []

        # Enter case
        if rd is None:
            rd, aparta = next(iter(self.aparta.items()))
            self.konsol.log(f"[yellow]Hanterar aparta följder av {rd.ord}")
            lyckat, knoppar = self.hantera_aparta(rd, aparta)
            if lyckat:
                self.konsol.log(f"[dark_sea_green4]{rd.ord} fungerade :smiley: :smiley: :smiley:")
                for kn in knoppar:
                    if kn not in self.ord:
                        self.konsol.log(f"[red3]{rd.ord} WTF")
                return True
            else:
                self.konsol.log(f"[red3]{rd.ord} fungerade inte")
                self.ångra(rd)
                for n in knoppar:
                    self.ångra(n)
                self.aparta.pop(rd, None)
                return False

        aparta_str = ", ".join([a.ord for a in aparta])
        self.konsol.log(f"Hanterar biverkningar av ordet {rd.ord}: [plum1]{aparta_str}[/plum1]")
        for apa in aparta:
            if apa not in self.ordlista and (3 < len(apa.ord) or not self.ordlista.kompatibla(apa.ord)):
                self.konsol.log(f"[plum1]{rd.ord}[/plum1] kastades eftersom [deep_pink4]{apa.ord}[/deep_pink4] är ogiltigt")
                return False, nya

        for apa in aparta:
            self.konsol.log(f"Hanterar [yellow]{apa.ord}...")
            if not apa in self.alla_ord():
                self.konsol.log(f"{apa.ord} har försvunnit ur rutnätet...")
                continue 
            
            korshår = self[apa.läge.slice()]
            kompatibla = self.ordlista.kompatibla(apa.ord)
            if apa in self.ordlista:
                self.konsol.log(f"[dark_sea_green4]{apa.ord} finns redan i ordlistan...")
                kompatibla += [Ord(*astuple(apa)).reset()]
            
            for m in korshår.möjligheter(reversed(kompatibla), enbart=Riktning(apa.läge.z), cache_w=False, cache_r=True, töm=False, överskrift=True):
                biverkningar = self.sätt(m)
                if not biverkningar:
                    nya.append(m)
                    self.konsol.log(f"[dark_sea_green4]{m.ord} gav inga biverkningar...")
                    break
                lyckat, knoppar = self.hantera_aparta(m, biverkningar)
                if lyckat:
                    nya.append(m)
                    nya += knoppar
                    self.konsol.log(f"[dark_sea_green4]Biverkningar från {m.ord} kunde hanteras...")
                    break
                else:
                    self.konsol.log(f"[plum1]Biverkningar från {m.ord} kunde inte hanteras...")
                    self.ångra(m)
                    for kn in knoppar:
                        self.ångra(kn)
                    self.aparta.pop(m, None)
                    continue
            else:
                self.konsol.log(f"[plum1]{rd.ord}[/plum1] kastades eftersom {apa} inte hade några bra hakningar...")
                return False, nya

        self.aparta.pop(rd)
        self.konsol.log(f"[dark_sea_green4]Behåller [light_sea_green]{rd.ord}[/light_sea_green] för tillfället...[/dark_sea_green4]")
        return True, nya

    def ångra(self, ord: Ord):
        self.konsol.log(f"[red3] ångrar {ord.ord}...")
        self.ord.reverse()
        self.ord.remove(ord)
        self.ord.reverse()
        return self

    def rensa(self):
        rens = []
        for rd in self.ord:
            längre = [dvrg for dvrg in self.ord if rd.läge.lägeskänslig(dvrg.läge) and len(dvrg) < len(rd)]
            rens += längre
        self.ord = [rd for rd in self.ord if not next((True for ren in rens if rd.lägeskänslig(ren)), False)]


    def starta(self):
        startord = [o for o in self.ordlista.ord if o.special]
        start = choice(string.ascii_letters).upper()
        kors = choice(list(self.kors.values()))
        self.sätt(Ord(start, kors.läge, False, False, False))
        start = kors.möjligheter(startord)
        self.sätt(next(start))
        return self

    def poängräkning(self):
        poäng = sum(o.poäng for o in self.ord)
        täckning = sum(
            (isinstance(bks, str) and bks.isalpha() for r in self.rader() for bks in r)
        )
        täckning = täckning / (self.bredd * self.höjd)
        medel = mean(len(o.ord) for o in self.ord) if self.ord else 0
        return poäng * medel * täckning



@lru_cache(maxsize=2000000)
def giltig(uno, dos):
    return uno == dos or dos is Ruta.TOM


@lru_cache(maxsize=2000000)
def passar(rd: Ord, bks: tuple[str]):
    if len(bks) < len(rd):
        return False
    return all((giltig(o, b) for o, b in zip(rd, bks)))

class Riktning(int, Enum):
    HORISONTELLT = 0
    VERTIKALT = 1
    BÅDA = 2
    INGA = 3    

@dataclass(unsafe_hash=True, repr=False)
class Kors:
    __slots__ = ["läge", "korsord", "tömd", "cache"]
    läge: Läge
    korsord: Korsord
    tömd: Riktning
    cache: dict[Ord, bool]

    def __lt__(self, kmp: Kors):
        return self.läge < kmp.läge

    def __repr__(self):
        return f"<Kors @ {self.läge!r} | {self.origo}>"

    @property
    def rad(self):
        return self.korsord.rader()[self.läge.x]

    @property
    def kol(self):
        return self.korsord.kolumner()[self.läge.y]

    @property
    def origo(self):
        return self.rad[self.läge.y]

    @property
    def gåta(self):
        return self.origo == Ruta.BLOCK.value

    @property
    def tom(self):
        return self.origo is Ruta.TOM

    @property
    def n(self):
        return self.kol[0 : self.läge.x]

    @property
    def e(self):
        return self.rad[self.läge.y + 1 :]

    @property
    def s(self):
        return self.kol[self.läge.x + 1 :]

    @property
    def w(self):
        return self.rad[0 : self.läge.y]

    def _låst(self, riktningar: str):
        ix = {"w": -1, "n": -1}
        låsta = [
            (not getattr(self, d) or getattr(self, d)[ix.get(d, 0)] is not Ruta.TOM)
            for d in riktningar
        ]
        return all(låsta)

    def _friheter(self, riktning):
        step = {"n": -1, "w": -1}
        fria = list(takewhile(lambda x: x is Ruta.TOM, getattr(self, riktning)[::step.get(riktning, 1)]))
        return len(fria)

    @property
    def friheter_horisontellt(self):
        return self._friheter("w") + self._friheter("e")

    @property 
    def friheter_vertikalt(self):
        return self._friheter("n") + self._friheter("s")

    @property
    def tomma(self):
        return self.rad.count(Ruta.TOM) + self.kol.count(Ruta.TOM)

    @property
    def kant(self):
        return self.läge.kant

    @property
    def vikt(self):
        return self.läge.x * self.läge.y

    @property
    def låst(self):
        return self._låst("nesw")

    @property
    def mellanrum_e(self):
        if tomma := self._friheter("e"):
            if not tomma < len(self.e):
                return None    
            if self.e[tomma] == Ruta.BLOCK.value:
                return None
            return self.origo, self.e[tomma], tomma

    @property
    def mellanrum_s(self):
        if tomma := self._friheter("s"):
            if not tomma < len(self.s):
                return None    
            if self.s[tomma] == Ruta.BLOCK.value:
                return None
            return self.origo, self.s[tomma], tomma

    def låst_horisontellt(self):
        return self._låst("we")

    def låst_vertikalt(self):
        return self._låst("ns")

    def funkar(self, rd: Ord, vertikalt=True):
        förekomst = rd.förekomst(self.origo)
        if not förekomst:
            return False
        orientering = (self.n, self.s) if vertikalt else (self.w, self.e)
        före, efter = orientering
        
        # mät mellan block i raden
        if Ruta.BLOCK.value in före:
            före = före[::-1].index(Ruta.BLOCK.value) + 1
        else:
            före = len(före)
        if Ruta.BLOCK.value in efter:
            efter = efter.index(Ruta.BLOCK.value) + 1
        else:
            efter = len(efter)
        
        omf = len(rd)
        if self.gåta:
            return omf <= efter
        svämmar = [
            0 <= (före - (pos - 1) <= 0) and 0 <= efter - (omf - pos + 1)
            for pos in förekomst
        ]
        passar = any(svämmar)
        if len(rd.ord) < 3 and not passar:
            self.korsord.konsol.log(f"[plum1] {rd.ord} passade inte in även fast det bara är två bokstäver...")
        return passar

    def möjligheter(self, kompatibla: list[ord], gräns=None, enbart=Riktning.BÅDA, överskrift=False, cache_r=True, cache_w=True, töm=True):
        self.korsord.konsol.log(f"Genererar möjligheter för kompatibla ord vid {self.läge!r}...")
        if cache_r:
            kompatibla = (k for k in kompatibla 
            if not self.cache.get(k, Riktning.INGA) is enbart 
            and not self.cache.get(k, Riktning.INGA) is Riktning.BÅDA)
        for ix, rd in enumerate(kompatibla, start=1):
            if len(rd.ord) == 2:
                self.korsord.konsol.log(f"{self!r}: kontrollerar {rd.ord}...")
            
            # Tillåt hakningar att användas fler än en gång
            if rd in self.korsord and 2 < len(rd.ord):
                continue
            if cache_w:
                if self.cache.get(rd):
                    self.cache[rd] = Riktning.BÅDA
                else:
                    self.cache[rd] = enbart
            yield from self.möjligheter_med(rd, överskrift, enbart)
            if gräns and gräns < ix:
                break
        else:
            if töm:
                if self.tömd is Riktning.INGA:
                    self.tömd = enbart
                elif self.tömd is Riktning.VERTIKALT and enbart is Riktning.HORISONTELLT:
                    self.tömd = Riktning.BÅDA
                elif self.tömd is Riktning.HORISONTELLT and enbart is Riktning.VERTIKALT:
                    self.tömd = Riktning.BÅDA
                
            self.korsord.konsol.log(f"[orange3]{self!r}: inga fler kompatibla...")
                
        
    def möjligheter_med(self, rd: Ord, överskrift, enbart=None):
        ns = enbart is Riktning.VERTIKALT
        we = enbart is Riktning.HORISONTELLT

        if not we and not (not överskrift and self.låst_vertikalt()):
            yield from self.i(rd, 1)
        if not ns and not (not överskrift and self.låst_horisontellt()):
            yield from self.i(rd, 0)

    def skapa_läge(self, ix, z):
            if z:
                läge = Läge(self.läge.x - ix, self.läge.y, 1) 
            else:
                läge = Läge(self.läge.x, self.läge.y - ix, 0)
            return läge

    def i(self, rd: Ord, z: int = 0):
        pre = self.n if z else self.w
        ps = self.s if z else self.e
        axel = self.kol if z else self.rad

        space1, space2 = len(pre), len(ps)
        förekommer = rd.förekomst(self.origo)
        #är_sub = self.korsord.ordlista.kompatibla(rd.ord)
        #är_sub = [kmp for kmp in är_sub if not kmp == rd]
        #if 0 < len(är_sub):
        #    sub_före = 0 < min(
        #        [max(m.förekomst(rd.ord), default=0) for m in är_sub],
        #        default=0,
        #    )
        #    sub_efter = 0 < max(
        #        [min(m.förekomst(rd.ord), default=0) for m in är_sub],
        #        default=0,
        #    )
        #else:
        #    sub_före, sub_efter = False, False
        if self.gåta:
            förekommer = [0, len(rd)]
        for ix in förekommer:
            kp = Ord(*astuple(rd)).positionera(self.skapa_läge(ix, z))
            if self.gåta:
                if ix == 0:
                    if (z and self._låst("s")) or (not z and self._låst("e")):
                        continue
                    kp.positionera(kp.läge)
                    if kp.läge.x < 0 or kp.läge.y < 0:
                        continue
                    startar = kp.läge.x if z else kp.läge.y
                    if len(axel) - startar < len(rd):
                        continue
                    går = passar(kp, tuple(axel[kp.läge.x if z else kp.läge.y:]))
                    if not går:
                        continue
                    yield kp
                else:
                    if (z and self._låst("n")) or (not z and self._låst("w")):
                        continue
                    #if not sub_före:
                    #    kp.stäng()

                    if kp.läge.x < 0 or kp.läge.y < 0:
                        continue
                    startar = kp.läge.x if z else kp.läge.y
                    if len(axel) - startar < len(rd):
                        continue
                    går = passar(kp, tuple(axel[startar:]))
                    if not går:
                        continue
                    yield kp
                
            else:
                #if not sub_före or kp.läge.kant:
                #    kp.stäng()
                #    ix += 1
                #if not sub_efter:
                #    kp.blockera(post=True)
                if kp.läge.x < 0 or kp.läge.y < 0:
                    continue
                går = passar(kp, tuple(axel[space1 - ix :]))
                if not går:
                    continue
                
                yield kp
        

class Inkompatibel(Exception):
    def __init__(self, ord=None, för=None):
        super().__init__()
        self.ord = ord
        self.för = för


class Fortare(Exception):
    pass


def generera(korsord: Korsord, tidsgräns=60) -> Korsord:
    möjligt = korsord.möjligheter()
    c = console.Console()
    with Live(korsord, console=korsord.konsol, auto_refresh=False) as live:
        
        while True:
            try:
                mh = next(möjligt, None)
                if not mh:
                    break
                antal = len(korsord.ord)
                korsord.sätt(mh)
                if korsord.aparta:
                    korsord.hantera_aparta()
                if mh in korsord:
                    korsord.rensa()
                    möjligt.throw(Fortare())

                live.refresh()
            except KeyboardInterrupt:
                live.refresh()
                break 
    return korsord


def main(tidsgräns=None):
    with Ordlista() as ordlista:
        with Korsord(20, 20, ordlista, console.Console()) as korsord:
            gen = generera(korsord, tidsgräns=tidsgräns)


if __name__ == "__main__":
    main()
