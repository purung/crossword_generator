from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field, astuple
from pathlib import Path

from rich.live import Live
from rich.traceback import install
from rich import print
from random import choice, randrange, sample
from collections import deque
from itertools import takewhile, cycle
from operator import attrgetter, itemgetter
from statistics import mean
import datetime
from functools import lru_cache
import re

install(show_locals=True)


class Ruta(str, Enum):
    TOM = "□"
    BLOCK = "■"

    def __repr__(self) -> str:
        return str(self.value)


@dataclass(unsafe_hash=True)
class Läge:
    x: int
    y: int
    z: int = field(default=0)


@dataclass(unsafe_hash=True)
class Ord:
    ord: str
    läge: Läge = None
    special: bool = field(compare=False, default=False, repr=False)
    pre: bool = field(compare=False, default=True)
    post: bool = field(compare=False, default=True)

    def __post_init__(self):
        self.ord = self.ord.strip(f"\n{Ruta.BLOCK} ")

    def __len__(self):
        return len(str(self)) - 1

    def __str__(self):
        return f"{Ruta.BLOCK if self.pre else ''}{self.ord}{Ruta.BLOCK if self.post else ''}"

    def __eq__(self, ord: str) -> bool:
        if isinstance(ord, Ord):
            return self.ord == ord.ord
        elif isinstance(ord, str):
            return self.ord == ord.strip("■").upper()
        return False

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
            return slice(self.läge.y, self.läge.y + len(self) + 1)
        return slice(self.läge.x, self.läge.x + (len(self)) + 1)

    @property
    def poäng(self):
        return len(self) * 2 if self.special else len(self)

    def positionera(self, läge: Läge):
        self.läge = läge
        return self

    def blockera(self, pre=None, post=None):
        if pre is not None:
            self.pre = pre
        if post is not None:
            self.post = post
        return self

    def reset(self):
        self.läge = None
        self.blockera(pre=True, post=True)
        return self

    @lru_cache
    def förekomst(self, bks: str) -> list[int]:
        st = [m.start() for m in re.finditer(bks, str(self))]
        return st


class Ordlista:
    def __init__(self, ord: list[Ord] = None):
        def ladda():
            laddade = []
            with Path("./special.txt").open() as specialfil:
                laddade += [Ord(o, special=True) for o in specialfil.readlines()]

            with Path("./words.txt").open() as vanligfil:
                laddade += [Ord(o) for o in vanligfil.readlines()]
            return laddade

        self.ord = ord or ladda()
        self.ord = sorted(self.ord, key=attrgetter("poäng"), reverse=True)
        self.förbrukade = []

    @lru_cache(maxsize=5000)
    def __contains__(self, ord: str) -> bool:
        """Ordet finns i ordlistan"""
        return next((True for o in self.ord if o == ord), False)

    def __getitem__(self, ord: str) -> Ord:
        return next(o for o in self.ord if o == ord)

    def __repr__(self) -> str:
        return f"<Ordlista med {len(self.ord)} ord>"

    def __iter__(self):
        return iter(self.ord)

    def __next__(self):
        return next(iter(self))

    def förbruka(self, ord):
        if not ord.kort:
            hittat = next(o for o in self.ord if o == ord)
            self.förbrukade.append(hittat)
        return self

    def ångra(self, ord):
        if ord in self.förbrukade:
            self.förbrukade.remove(ord)
        return self

    @property
    def lediga(self) -> set[str]:
        return set(self.ord).difference(set(self.förbrukade))

    def slumpad(self, special=False) -> Ord:
        if special:
            return choice([o for o in list(self.lediga) if o.special])
        return choice(list(self.lediga))

    def ordnade(self):
        yield from sorted(
            (o for o in self.lediga), key=attrgetter("poäng"), reverse=True
        )

    @lru_cache(maxsize=20000)
    def kompatibla(self, sub: str) -> list[Ord]:
        komp = [o for o in self.ord if o.förekomst(sub)]
        return komp


@dataclass
class Korshår:
    n: list[str]
    e: list[str]
    s: list[str]
    w: list[str]
    origo: str
    läge: Läge = field(repr=False)

    def fria(self, rkt: str) -> int:
        strk = getattr(self, rkt)
        if not rkt:
            return 0
        if rkt in "nw":
            strk = reversed(strk)
        return len(list(takewhile(lambda x: x is Ruta.TOM, strk)))

    @property
    def ns(self) -> str:
        return list(self.n) + [self.origo] + list(self.s)

    @property
    def we(self) -> str:
        return list(self.w) + [self.origo] + list(self.e)

    @property
    def inlåst(self) -> bool:
        return all((not self.fria(rkt) for rkt in "nesw"))

    def i(self, rd: Ord, z: int = 0) -> list[Läge]:
        lg = []
        pre = self.n if z else self.w
        ps = self.s if z else self.e
        axel = self.ns if z else self.we

        space1, space2 = len(pre), len(ps)

        for ix in rd.förekomst(self.origo):
            if space1 == len(rd[:ix]) - 1:
                rd.blockera(pre=False)
                ix -= 1
            if space2 == len(rd[ix + 1 :]) - 1:
                rd.blockera(post=False)
            för_kort = len(pre) - len(rd[:ix]) < 0
            för_lite = len(ps) - len(rd[ix + 1 :]) < 0
            if för_kort or för_lite:
                rd.reset()
                continue

            går = self.passar(rd, axel[space1 - ix :])
            if not går:
                rd.reset()
                continue
            if z:
                läge = Läge(max(0, self.läge.x - ix), self.läge.y, 1)
                kp = Ord(*astuple(rd)).positionera(läge)
                lg.append(kp)
            else:
                läge = Läge(self.läge.x, max(0, self.läge.y - ix), 0)
                kp = Ord(*astuple(rd)).positionera(läge)
                lg.append(kp)
        return lg

    @staticmethod
    def passar(rd: Ord, bks: list[str]):
        j1 = list(rd)
        j2 = bks
        return not any([not (o == b or b is Ruta.TOM) for o, b in zip(j1, j2)])

    def lägen(self, rd: Ord) -> iter[Läge]:
        lägen = []
        lägen += self.i(rd, 0)
        lägen += self.i(rd, 1)
        yield from lägen


@dataclass
class Korsord:
    höjd: int
    bredd: int
    ordlista: Ordlista = field(default=None, repr=False)
    ord: list[Ord] = field(default_factory=list, repr=False)
    aparta: deque[Ord] = field(default_factory=deque, repr=False)
    cache: list[Ord] = field(default_factory=list, repr=False)
    släng: list[Ord] = field(default_factory=list, repr=False)
    kors: dict[Läge, Kors] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        lägen = [
            Läge(x, y, z)
            for x, rad in enumerate(self.rader)
            for y, ltr in enumerate(rad)
            for z in (0, 1)
        ]
        self.kors.update({l: Kors(l, self) for l in lägen for l in lägen})

    def __str__(self) -> str:
        return "\n".join([" ".join(rad) for rad in self.rader])

    @property
    def __rutnät(self) -> list[list[str]]:
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
        return self.rader[skiva.start][skiva.stop]

    def __contains__(self, ord: str):
        return next((True for o in self.ord if o == ord), False)

    def __rich_console__(self, console, options):
        console.clear()
        png = f"\nPoäng: {self.poängräkning()}\n"
        senast = f"Senaste tillagda ordet: {self.ord[-1]!r}\n"
        senaste = f"Senaste omöjliga orden: {', '.join(str(o) for o in self.släng[:-10:-1])}\n"
        chanser = (
            f"Senast prövade ord: {', '.join(str(o) for o in self.cache[:-10:-1])}\n"
        )
        yield str(self) + png + senast + senaste + chanser

    @property
    def rader(self) -> list[list[str]]:
        """Skapa rader"""
        return self.__rutnät

    @property
    def kolumner(self) -> list[list[str]]:
        """Rotera rader till kolumner"""
        return list(zip(*self.rader))

    def hitta(self, bks: str) -> list[tuple[int, int]]:
        """Se alla koordinater för en viss bokstav"""
        if not len(bks) == 1:
            return []
        bks = bks.upper()
        return [
            Läge(x, y)
            for x, rad in enumerate(self.rader)
            for y, ltr in enumerate(rad)
            if bks == ltr
        ]

    def _ord_i_lista(self, rad: list[str]) -> list[str]:
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

    def horisontella_ord(self) -> list[Ord]:
        """Alla ord som bildas längsmed rader"""

        def lg(ix, o):
            return Läge(ix, max(0, "".join(self.rad(ix)).find(o)), 0)

        return [
            Ord(o, lg(ix, o), pre=False, post=False)
            for ix, rad in enumerate(self.rader)
            for o in self._ord_i_lista(rad)
            if 1 < len(o)
        ]

    def vertikala_ord(self) -> list[Ord]:
        """Alla ord som bildas längsmed kolumner"""

        def lg(ix, o):
            return Läge(max(0, "".join(self.kolumn(ix)).find(o)), ix, 1)

        return [
            Ord(o, lg(ix, o), pre=False, post=False)
            for ix, kol in enumerate(self.kolumner)
            for o in self._ord_i_lista(kol)
            if 1 < len(o)
        ]

    def alla_ord(self) -> list[Ord]:
        """Alla ord som bildas i korsordet"""
        alla = [*self.horisontella_ord(), *self.vertikala_ord()]
        return alla

    def rad(self, ix: int) -> list[str]:
        return self.rader[ix]

    def kolumn(self, ix: int) -> list[str]:
        return self.kolumner[ix]

    def korshår(self, läge: Läge) -> Korshår:
        return next(k for k in self.kors if k.läge == läge)

    def är_gilgigt(self) -> bool:
        """Alla bildade ord är i ordlistan"""
        return all(True for o in self.alla_ord if o in self.ordlista)

    def avslöja_aparta(self):
        ord_just_nu = self.alla_ord()
        friade = [o for o in self.aparta if o not in ord_just_nu]
        for o in friade:
            self.aparta.remove(o)
        fällda = [o for o in ord_just_nu if o not in self.ord and o not in self.aparta]
        self.aparta += fällda

        return self

    def sätt(self, rd: Ord):
        self.ord.append(rd)
        self.cache.append(rd)
        self.ordlista.förbruka(rd)
        self.avslöja_aparta()
        return self

    def möjligheter_för_ord(self):
        lista = self.ordlista.ordnade()

        for bästa in lista:
            try:
                bkvs = list(bästa)
                bkvs = sample(bkvs, len(bkvs))
                for bks in bkvs:
                    lägen = (
                        kors
                        for kors in self.kors.values()
                        if not kors.tom and not kors.låst and kors.origo == bks
                    )
                    mh = (kors for kors in lägen if kors.kompatibelt_med(bästa))
                    mjh = (
                        m
                        for kors in mh
                        for m in kors.möjligheter_med(bästa)
                        if m not in self.cache
                    )
                    minst_biverkningar = []
                    for pröva in mjh:
                        self.cache.append(pröva)
                        antal = self.biverkningar(pröva)
                        if antal[0] is None:
                            continue
                        if antal[0] == 0:
                            yield pröva
                        minst_biverkningar.append((antal, pröva))
                    if not minst_biverkningar:
                        continue
                    yield min(minst_biverkningar, key=itemgetter(0))[1]
            except Fortare:
                continue

    def biverkningar(self, rd: Ord):
        antal_aparta = len(self.aparta)
        self.sätt(rd)
        antal = antal_aparta - len(self.aparta)
        if not antal:
            self.ångra()
            return 0, rd
        try:
            self.hantera_inkompatibla()
        except Inkompatibel:
            self.ångra()
            return None, rd
        self.ångra()
        return antal, rd

    def generera_kors(self):
        kors = [k for k in self.kors.values() if not k.låst and not k.tom]
        if kors:
            yield choice(kors)

    def möjligheter(self):
        kors = next(self.generera_kors())
        while True:
            try:
                for o in self.ordlista.kompatibla(kors.origo):
                    mh = (
                        mh for mh in kors.möjligheter_med(o) if kors.kompatibelt_med(o)
                    )
                    m = (c for c in mh if not c in self.cache)
                    for möjlighet in m:
                        yield möjlighet
                kors = next(self.generera_kors())
            except Fortare:
                kors = next(self.generera_kors())
                continue

    def flätade_möjligheter(self):
        prio = self.möjligheter_för_ord()
        alla = self.möjligheter()
        cykel = cycle((*(prio for _ in range(3)), *(alla for _ in range(150))))
        for gen in cykel:
            try:
                yield next(gen)
            except Fortare:
                gen.throw(Fortare())

    def hantera_inkompatibla(self):
        kompatibla = []
        for o in [a for a in self.aparta]:
            if o in self.släng:
                raise Inkompatibel()
            if o in self.ordlista:
                kompatibla.append((o, [o]))
                continue
            komp = list(self.ordlista.kompatibla(o.ord))
            if not komp:
                self.släng.append(o)
                raise Inkompatibel()
            kompatibla.append((o, komp))
        return kompatibla

    def hantera_aparta(self):
        while self.aparta:
            try:
                a = self.aparta.pop()
                self.hantera_apart(a)
            except Inkompatibel:
                self.ångra()
        return self

    def hantera_apart(self, ord: Ord):
        if not ord.läge:
            raise ValueError
        if ord in self.släng:
            raise Inkompatibel()
        korshår = self.kors[ord.läge]
        if ord in self.ordlista and ord not in self.cache:
            möjligheter = [ord]
        else:
            kompatibla = list(self.ordlista.kompatibla(ord.ord))
            if not kompatibla:
                self.släng.append(ord)
                raise Inkompatibel()
            möjligheter = list(
                mh
                for o in kompatibla
                for mh in korshår.möjligheter_med(o)
                if mh not in self.cache
            )
        if redan_där := next((m for m in möjligheter if m == ord), None):
            self.sätt(redan_där)
            print(self)
            return True
        if möjligheter:
            self.sätt(choice(möjligheter))
            print(self)
            return True
        raise Inkompatibel()

    def ångra(self):
        ånger = self.ord.pop()
        self.ordlista.ångra(ånger)
        self.avslöja_aparta()
        return self

    def starta(self):
        startord = [o for o in self.ordlista if o.special]
        startord = [o for o in startord if len(o) <= self.bredd and len(o) <= self.höjd]
        if not startord:
            raise Inkompatibel
        startord = choice(startord)
        passande_höjd = (
            0 if len(startord) == self.höjd else randrange(0, self.höjd - len(startord))
        )
        passande_bredd = (
            0
            if len(startord) == self.bredd
            else randrange(0, self.bredd - len(startord))
        )
        läge = Läge(passande_höjd, passande_bredd, randrange(0, 2))
        self.sätt(startord.positionera(läge))
        return self

    def poängräkning(self):
        poäng = sum(o.poäng for o in self.ord)
        täckning = sum(
            (isinstance(bks, str) and bks.isalpha() for r in self.rader for bks in r)
        )
        täckning = täckning / (self.bredd * self.höjd)
        medel = mean(len(o.ord) for o in self.ord)
        return poäng * medel * täckning


@lru_cache(maxsize=5000)
def passar(rd: Ord, bks: str):
    ihop = list(zip(rd, bks))
    passar = not any([(not o == b and not b == Ruta.TOM.value) for o, b in ihop])
    return passar


@dataclass(unsafe_hash=True)
class Kors:
    läge: Läge
    korsord: Korsord = field(repr=False, compare=False)

    @property
    def rad(self):
        return self.korsord.rader[self.läge.x]

    @property
    def kol(self):
        return self.korsord.kolumner[self.läge.y]

    @property
    def origo(self):
        return self.korsord[self.läge.x : self.läge.y]

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

    @property
    def låst(self):
        riktningar = [
            (not getattr(self, d) or getattr(self, d)[0] is not Ruta.TOM)
            for d in "nesw"
        ]
        return all(riktningar)

    @lru_cache(maxsize=5000)
    def kompatibelt_med(self, rd: Ord):
        if self.tom:
            return False
        fritt = max((len(self.e), len(self.s)))
        uppåt = min((len(self.n), len(self.w)))
        if self.gåta:
            return len(rd) <= fritt
        förekomst = rd.förekomst(self.origo)
        if not förekomst:
            return False
        funkar = all([(len(rd) - max(förekomst) <= fritt), (min(förekomst) <= uppåt)])
        return funkar

    def möjligheter_med(self, rd: Ord):
        yield from self.i(rd, 0)
        yield from self.i(rd, 1)

    def i(self, rd: Ord, z: int = 0):

        pre = self.n if z else self.w
        ps = self.s if z else self.e
        axel = self.kol if z else self.rad

        space1, space2 = len(pre), len(ps)
        förekommer = rd.förekomst(self.origo)
        är_sub = self.korsord.ordlista.kompatibla(rd.ord)
        if 0 < len(är_sub):
            sub_före = 0 < min(
                [max(m.förekomst(rd.ord), default=0) for m in är_sub if not m == rd],
                default=0,
            )
            sub_efter = 0 < max(
                [min(m.förekomst(rd.ord), default=0) for m in är_sub if not m == rd],
                default=0,
            )
        else:
            sub_före, sub_efter = False, False
        for ix in rd.förekomst(self.origo):
            if space1 == len(rd[:ix]) - 1 or sub_före:
                rd.blockera(pre=False)
                ix -= 1
            if space2 == len(rd[ix + 1 :]) - 1 or sub_efter:
                rd.blockera(post=False)
            för_kort = len(pre) - len(rd[:ix]) < 0
            för_lite = len(ps) - len(rd[ix + 1 :]) < 0
            if för_kort or för_lite:
                rd.reset()
                continue

            går = passar(rd, "".join(axel[space1 - ix :]))
            if not går:
                rd.reset()
                continue
            if z:
                läge = Läge(max(0, self.läge.x - ix), self.läge.y, 1)
                kp = Ord(*astuple(rd)).positionera(läge)
                yield kp
            else:
                läge = Läge(self.läge.x, max(0, self.läge.y - ix), 0)
                kp = Ord(*astuple(rd)).positionera(läge)
                yield kp

            rd.reset()


class Inkompatibel(Exception):
    def __init__(self, ord=None):
        super().__init__()
        self.ord = ord


class Fortare(Exception):
    pass


def generera(korsord: Korsord, tidsgräns=60) -> Korsord:
    möjligt = korsord.möjligheter_för_ord()
    stamp = datetime.datetime.now() + datetime.timedelta(seconds=tidsgräns)
    while datetime.datetime.now() < stamp:
        print(korsord)
        mh = next(möjligt, None)
        if not mh:
            break
        antal = len(korsord.ord)
        korsord.sätt(mh)
        if korsord.aparta:
            korsord.hantera_aparta()
        if mh in korsord:
            möjligt.throw(Fortare())
        if 50 < korsord.poängräkning():
            möjligt = korsord.möjligheter()
    return korsord


def spara(korsord):
    with Path("./sparade.txt").open(mode="a", encoding="utf-8") as bank:
        bank.write(str(korsord))
        bank.write(f"\nPoäng: {korsord.poängräkning()}\n\n")


def bygg_vidare(korsord):
    spara(generera(korsord, tidsgräns=900))


def main(tidsgräns=1200):
    for _ in range(5):
        ordlista = Ordlista()
        korsord = Korsord(20, 20, ordlista)
        korsord.starta()
        gen = generera(korsord, tidsgräns=tidsgräns)
        spara(gen)


if __name__ == "__main__":
    bygg_vidare(main())
