import shapefile
from fltk import *
import math
import main2
def open_shapefile():
    path = "departements-20180101-shp/departements-20180101.shp"
    sh_file = shapefile.Reader(path)
    return sh_file


sh_file = open_shapefile()

def trie_sh():
    resultat = []
    records = sh_file.records()
    shapes = sh_file.shapes()

    for rec, shp in zip(records, shapes):
        code_dep = rec[0]  

        if code_dep in ['971', '972', '973', '974', '976']:  
            continue
        resultat.append(shp)

    return resultat,records



xmin, ymin, xmax, ymax = sh_file.bbox
all_shapes, records = trie_sh()

class GeoScale:
    def __init__(self, xmin, ymin, xmax, ymax, largeur, hauteur, aspect=True):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.largeur = largeur
        self.hauteur = hauteur
        self.aspect = aspect


        dx = xmax - xmin
        dy = ymax - ymin #Диапазон между макс и мин координатoi

        sx = self.largeur / dx
        sy = self.hauteur / dy
        self.scale = min(sx, sy)

        map_larg = dx * self.scale
        map_haut = dy * self.scale
        self.offset_x = (largeur - map_larg) / 2
        self.offset_y = (hauteur - map_haut)   #tabs for having a map in the middle


    # ça marche mais c'est un peu brouillon ?
    def from_geo_to_pix(self, lon, lat):
        # lat_rad = math.radians(lat)
        x = (lon - self.xmin) * self.scale + self.offset_x
        y = (self.ymax - math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))) * self.scale + self.offset_y
        return x, y  

scale = GeoScale(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, largeur=800, hauteur=800)

cree_fenetre(scale.largeur, scale.hauteur)


def draw_shape(shape):
    pnts = shape.points #tous les points de polygone
    prts = list(shape.parts) + [len(pnts)]  #toutes les parties de polygone, on ajoute len pour qu'on puisse
                                            # obtenir le dernier point, pour qu'on puisse
                                              # quand il faut finit de faire dernier polyg
    for i in range(len(prts)-1):
        segment = pnts[prts[i]:prts[i+1]] #partage par des segments (on ecrit les points de ca ([0:150]))
        segment_pixels = []
        for lon, lat in segment:
            coords = scale.from_geo_to_pix(lon, lat)
            segment_pixels.append(coords)
        polygone(segment_pixels, couleur = "black")


for shape in all_shapes:
    draw_shape(shape)



def boutons ():
    ligne(0)



# Permet de se déplacer sur la carte avec les touches directionnelles
def se_deplacer(speed=10):
    dx = dy = 0
    if touche_pressee("Left"):
        dx += speed
    if touche_pressee("Right"):
        dx -= speed
    if touche_pressee("Up"):
        dy += speed
    if touche_pressee("Down"):
        dy -= speed
    if dx != 0 or dy != 0:
        deplace("all", dx, dy)
        
while True:
    se_deplacer()
    mise_a_jour()
    
    ev = donne_ev()
    if type_ev(ev) == 'Quitte':
            break

ferme_fenetre()
