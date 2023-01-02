from korsord.rutnät import mellanrum, Ruta, fyller_mellanrum

from rich import print


if __name__ == "__main__":
    #print(mellanrum("".join([Ruta.TOM, "J"])))
    #print(mellanrum(Ruta.TOM + Ruta.TOM))
    #print(mellanrum(""))

    print(fyller_mellanrum("A", "M", "ARM"))
    print(fyller_mellanrum("A", "M", "KAR"))
    print(fyller_mellanrum("A", "M", "KRAM"))
    print(fyller_mellanrum("A", "M", "KARM"))
    print(fyller_mellanrum("A", "M", "KARRM"))