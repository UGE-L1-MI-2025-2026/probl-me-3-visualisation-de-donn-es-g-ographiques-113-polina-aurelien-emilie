import shapefile
from fltk import *
import math
def open_shapefile():
    path = "departements-20180101-shp/departements-20180101.shp"
    sh_file = shapefile.Reader(path)
    return sh_file

sh_file = open_shapefile()

xmin, ymin, xmax, ymax = sh_file.bbox
all_shapes = sh_file.shapes()

class GeoScale:
    def __init__(self, xmin, ymin, xmax, ymax, largeur, hauteur, zoom):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.largeur = largeur
        self.hauteur = hauteur
        self.zoom = zoom


        dx = xmax - xmin
        dy = ymax - ymin #Диапазон между макс и мин координатoi

        sx = self.hauteur / dx
        sy = self.largeur / dy #Коэффицент масштабирования, чтобы карта не расплющивалась
        self.scale = min(sx, sy)
        print(self.scale)
        

        map_larg = dx * self.scale
        map_haut = dy * self.scale
        print(map_larg, map_haut)
    
        self.offset_x = (largeur - map_larg) / 2
        self.offset_y = (hauteur - map_haut)   #tabs for having a map in the middle
        print(self.offset_x, self.offset_y)
        
    '''
    def from_geo_to_pix(self, lon, lat):
        lon_rad = math.radians(lon)
        lat_rad = math.radians(lat)

        x = (lon_rad - self.xmin) + self.offset_x
        x*= self.scale 
        y =  math.log(math.tan(math.pi / 4 + lat_rad / 2))+self.offset_y
        y *= self.scale
        return x, y

    ''' 
    # ça marche mais c'est un peu brouillon ?
    def from_geo_to_pix(self, lon, lat):
        # lat_rad = math.radians(lat)
        x = (lon - self.xmin) * (self.scale * self.zoom) + self.offset_x 
        y = (self.ymax - math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))) * (self.scale * self.zoom) + self.offset_y 
        return x, y  
    
    def zoomer(self, facteur):
        
        # coordonnées centre carte
        cx = self.largeur / 2
        cy = self.hauteur / 2
        
        # nouveaux offsets (pour centrer la carte lors du zoom)
        self.offset_x = cx - (cx - self.offset_x) * self.zoom
        self.offset_y = cy - (cy - self.offset_y) * self.zoom
        
        self.zoom *= facteur
        # à revoir ! (zoom non centré, décalage vers droite et bas)
    
scale = GeoScale(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, largeur=800, hauteur=800, zoom = 1.0)

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

# Repère (à supprimer ?) A REVOIR ! 
'''
def affiche_centre():
    l1 = ligne(scale.largeur / 2 - 10, scale.hauteur / 2, scale.largeur / 2 + 10, scale.hauteur / 2)
    l2 = ligne(scale.largeur / 2, scale.hauteur / 2 - 10, scale.largeur / 2, scale.hauteur / 2 + 10)
    
    if se_deplacer() == True:
        efface(l1)
        efface(l2)
        mise_a_jour()  
    
    
def affiche_zoom():
    new_zoom = scale.zoom
    
    rect1 = rectangle(scale.largeur - 70, scale.hauteur - 40, scale.largeur - 5, scale.hauteur - 10)
    txt_zoom = texte(scale.largeur - 66 , scale.hauteur - 30, f"Zoom : {round(new_zoom, 2)}", taille = 8)
   
def truc():
    d = d

def affiche_temps():
    d = d
'''

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
    ev = donne_ev()
    se_deplacer()
    '''
    affiche_centre()
    affiche_zoom()
    '''
    mise_a_jour()
    
    if touche_pressee("z"):
        scale.zoomer(ZOOM)
        efface_tout()
        dessine_carte()
        
    if touche_pressee("d"):
        scale.zoomer(DZOOM) 
        efface_tout()
        dessine_carte()
    
    if type_ev(ev) == 'ClicGauche':
        d=d
    
    if type_ev(ev) == 'Quitte':
        break
    

ferme_fenetre()



