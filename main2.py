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
    resultat = []
    tab = open_file()

    for colonnes in tab:
        # colonnes = [date, code_dept, nom_dept, tmin, tmax, tavg]
        if len(colonnes) < 3:
            continue

        # filtre : département = Paris
        if colonnes[2] == "Paris":
            resultat.append(colonnes)  # ajoute le sous-tableau entier

    return resultat


def convertisseur ():
    d=d


def afficher_restaurant():
    d=d

def WGS_Mercator ():
    """convert WGS data to Mercator data"""
    d=d

def Mercator_WGS ():
    """convert Mercator data to WGS data"""
    d=d    

print(trie())