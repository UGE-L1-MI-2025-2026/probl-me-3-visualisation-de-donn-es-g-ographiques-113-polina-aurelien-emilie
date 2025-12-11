from shapefile import*
from fltk import*
import re


def open_file():
    lignes = []

    with open("temperature-quotidienne-departementale.csv") as f:
        for ligne in f:
            ligne = ligne.strip()          # retire \n
            if ligne == "":
                continue
            colonnes = ligne.split(";")    # transforme la ligne en tableau
            lignes.append(colonnes)        # ajoute le tableau de colonnes
    return lignes



def trie():
    resultat = open_file()
    return resultat
