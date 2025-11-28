from shapefile import*
from fltk import*
import re

def open_file():
    tab=[]
    with open("temperature-quotidienne-departementale.csv") as f:
        read=f.read()
        read=re.split(";|\n",read)
        tab.append(read)
    return tab
            

def trie():
    paris=[]
    tab=open_file()
    for x in tab :
        if tab[x]=="Paris":
            paris.append(x[-2])
            paris.append(x[-1])
            paris.append(x)
            paris.append(x[1])
            paris.append(x[2])
            paris.append(x[3])
        else : 
            continue
    return paris
    

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