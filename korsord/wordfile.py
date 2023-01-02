from pathlib import Path
from rich import print, console, prompt
import xml.etree.ElementTree as ET
from random import choice
from functools import lru_cache

RESURS = Path("./words.txt")


@lru_cache
def load_words():
    with RESURS.open(encoding="utf-8") as ord:
        return ord.readlines()


def load_syn():
    with Path("./synpairs2.xml").open() as synfil:
        return ET.parse(synfil).find("synonyms")


def write_words(ord: list[str], mode="a"):
    ord = [o.upper() for o in ord]
    mål = Path("./words.txt")
    with mål.open(mode=mode, encoding="utf-8") as ordfil:
        for o in ord:
            if o:
                ordfil.write(o + "\n")
    return True


def mixtra(ord):
    redan = load_words()
    korta = list({s.text for o in ord for s in o if len(s.text) == 5 and s not in redan})
    korta = [s.strip("\n") for s in korta + redan if " " not in s]

    return korta 


def process(ord):
    resultat = []
    for _ in range(60):
        syn = choice(ord)
        while syn in load_words() or syn in resultat:
            syn = choice(ord)
        w = choice(syn)
        if prompt.Confirm.ask(f"[bold yellow]{w.text}"):
            resultat.append(w.text)
    return list(set(resultat))


def out(ord: set[str]):
    c = console.Console()
    for rd in ord:
        c.print(rd, style="blue bold", justify="center")


def unika():
    return list({s.strip("\n") for s in load_words()})


def main():
    rd = load_syn()
    mx = mixtra(rd)
    rd = sorted(mx, key=len, reverse=True)
    write_words(rd, mode="w")


if __name__ == "__main__":
    main()
