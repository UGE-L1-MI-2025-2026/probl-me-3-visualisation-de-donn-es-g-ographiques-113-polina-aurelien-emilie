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
    resultat_shapes = []
    resultat_records = []

    DROM = {'971','972','973','974','976'}
    records = sh_file.records()
    shapes = sh_file.shapes()

    for rec, shp in zip(records, shapes):
        code_dep = rec[0]  

        if code_dep not in DROM:  
            resultat_shapes.append(shp)
            resultat_records.append(rec)

    return resultat_shapes, resultat_records

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

def temp_par_departament():
    data = main2.trie()  # liste de liste
    temp_departament = {}
    for i in range(1, len(data)):
        if data[i][5] == '' :
            continue
        else:
            key = data[i][1]
            temp = float(data[i][5])
            temp_departament[key] = temp
    return temp_departament

def temp_to_color(temp, tmin, tmax):
    if tmax == tmin:
        norm = 0
    else:
        norm = (temp - tmin) / (tmax - tmin)
    r = int(255 * norm)
    g = 0
    b = int(255 - (255 - 0) * norm)
    return f'#{r:02x}{g:02x}{b:02x}'

temp_departament = temp_par_departament()
tmin = min(temp_departament.values())
tmax = max(temp_departament.values())
scale = GeoScale(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, largeur=800, hauteur=800)
cree_fenetre(scale.largeur, scale.hauteur)
x, y = 770, 0
temperature = -30


for i in range(-30, 40, 2):
    color = temp_to_color(i, -30, 40)
    if len(color) == 7:
        final_color = color
    #print(color, len(color))
    rectangle(x,y, x + 30, y + 12, remplissage = final_color)
    if int(i) % 10 == 0:
        texte(x-30, y, f'{int(i)} -', couleur = 'black', taille = 10)

    y += 12





def draw_shape(shape, record):
    depart_code = record[0]

    if depart_code in temp_departament.keys():
        temp = temp_departament[depart_code]
        depart_color = temp_to_color(temp, tmin, tmax)
        #print(depart_code, temp, depart_color)
    else:
        depart_color = None
    pnts = shape.points #tous les points de polygone
    prts = list(shape.parts) + [len(pnts)]  #toutes les parties de polygone, on ajoute len pour qu'on puisse
                                                # obtenir le dernier point, pour qu'on puisse savoir
                                                  # quand il faut finit de faire dernier polyg
    for i in range(len(prts)-1):

        segment = pnts[prts[i]:prts[i+1]] #partage par des segments (on ecrit les points de ca ([0:150]))
        segment_pixels = []
        for lon, lat in segment:
            coords = scale.from_geo_to_pix(lon, lat)
            segment_pixels.append(coords)
        #print(depart_color)
        polygone(segment_pixels, couleur = "black", remplissage = depart_color)


for shape, record in zip(all_shapes, records):
    draw_shape(shape, record)



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
    if type_ev(ev) == "ClicGauche":
        x = abscisse(ev)
        y = ordonnee(ev)
        """je suis en train d'essayer de faire un affichage de chaque polygone"""


ferme_fenetre()
