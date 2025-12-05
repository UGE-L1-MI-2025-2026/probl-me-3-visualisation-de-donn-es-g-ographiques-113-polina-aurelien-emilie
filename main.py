import shapefile
from fltk import *
import math
def open_shapefile():
    path = "departements-20180101-shp/departements-20180101.shp"
    sh_file = shapefile.Reader(path)
    return sh_file

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
        if colonnes[0]!="2024-05-13":
            continue

        else:
            resultat.append(colonnes)  # ajoute le sous-tableau entier

    return resultat

print(trie())
sh_file = open_shapefile()

xmin, ymin, xmax, ymax = sh_file.bbox
all_shapes = sh_file.shapes()

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

        sx = self.hauteur / dx
        sy = self.largeur / dy #Коэффицент масштабирования, чтобы карта не расплющивалась
        self.scale = min(sx, sy)
        print(self.scale)
        
        # zoom "de base"
        self.zoom = 1.0

        map_larg = dx * self.scale
        map_haut = dy * self.scale
        print(map_larg, map_haut)
    
        self.offset_x = (largeur - map_larg) / 2
        self.offset_y = (hauteur - map_haut)   #tabs for having a map in the middle
<<<<<<< HEAD

=======
        print(self.offset_x, self.offset_y)
        
    '''
    def from_geo_to_pix(self, lon, lat):
        lon_rad = math.radians(lon)
        lat_rad = math.radians(lat)
>>>>>>> 7901863ef5829ca445e7aaa312f5a6988d934a42

    # ça marche mais c'est un peu brouillon ?
    def from_geo_to_pix(self, lon, lat):
        # lat_rad = math.radians(lat)
        x = (lon - self.xmin) * (self.scale * self.zoom) + self.offset_x
        y = (self.ymax - math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))) * (self.scale * self.zoom) + self.offset_y
        return x, y  
<<<<<<< HEAD

=======
    
    def zoomer(self, facteur):
        self.zoom *= facteur
    
>>>>>>> 7901863ef5829ca445e7aaa312f5a6988d934a42
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


def dessine_carte():       
    for shape in all_shapes:
        draw_shape(shape)  

dessine_carte()

<<<<<<< HEAD

=======
>>>>>>> 7901863ef5829ca445e7aaa312f5a6988d934a42
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
       
 
        
# Permet de zoomer ou dézoomer la carte
ZOOM = 1.1
DZOOM = 1/1.1
    
while True:
    se_deplacer()
    mise_a_jour()
    
    if touche_pressee("z"):
        scale.zoomer(ZOOM)
        efface_tout()
        dessine_carte()
        
    if touche_pressee("d"):
        scale.zoomer(DZOOM) 
        efface_tout()
        dessine_carte()
    
    ev = donne_ev()
    if type_ev(ev) == 'Quitte':
        break
        

ferme_fenetre()
<<<<<<< HEAD
=======

>>>>>>> 7901863ef5829ca445e7aaa312f5a6988d934a42
