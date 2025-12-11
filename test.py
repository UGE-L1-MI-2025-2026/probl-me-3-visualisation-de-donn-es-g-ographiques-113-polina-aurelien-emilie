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
    def __init__(self, xmin, ymin, xmax, ymax, largeur, hauteur, aspect=True, database = None):

        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.largeur = largeur
        self.hauteur = hauteur
        self.aspect = aspect
        self.database = database if database is not None else {}


        dx = xmax - xmin
        dy = ymax - ymin  # Диапазон между макс и мин координатoi

        sx = self.largeur / dx
        sy = self.hauteur / dy
        self.scale = min(sx, sy)

        map_larg = dx * self.scale
        map_haut = dy * self.scale
        self.offset_x = (largeur - map_larg) / 2
        self.offset_y = (hauteur - map_haut)  # tabs for having a map in the middle

    # ça marche mais c'est un peu brouillon ?
    def from_geo_to_pix(self, lon, lat):
        x = (lon - self.xmin) * self.scale + self.offset_x
        y = (self.ymax - math.degrees(
            math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))) * self.scale + self.offset_y
        return x, y


def temp_par_departament():
    data = main2.trie()  # liste de liste
    temp_departament = {}
    for i in range(1, len(data)):
        if data[i][5] == '':
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
scale = GeoScale(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, largeur=800, hauteur=800, database= {})
cree_fenetre(scale.largeur, scale.hauteur)
x, y = 770, 0
temperature = -30

for i in range(-30, 40, 2):
    color = temp_to_color(i, -30, 40)
    if len(color) == 7:
        final_color = color
    # print(color, len(color))
    rectangle(x, y, x + 30, y + 12, remplissage=final_color, tag = "gradient")
    if int(i) % 10 == 0:
        texte(x - 30, y, f'{int(i)} -', couleur='black', taille=10, tag = "temp_valeur")

    y += 12


def draw_shape(shape, record, numero_depart):
    depart_code = record[0]

    if depart_code in temp_departament.keys():
        temp = temp_departament[depart_code]
        depart_color = temp_to_color(temp, tmin, tmax)
        # print(depart_code, temp, depart_color)
    else:
        depart_color = None
    pnts = shape.points  # tous les points de polygone
    prts = list(shape.parts) + [len(pnts)]  # toutes les parties de polygone, on ajoute len pour qu'on puisse
    # obtenir le dernier point, pour qu'on puisse savoir
    # quand il faut finit de faire dernier polyg
    polygone_pixels = []
    for i in range(len(prts) - 1):

        segment = pnts[prts[i]:prts[i + 1]]  # partage par des segments (on ecrit les points de ca ([0:150]))
        segment_pixels = []
        for lon, lat in segment:
            coords = scale.from_geo_to_pix(lon, lat)
            segment_pixels.append(coords)
            polygone_pixels.append(coords)

        polygone(segment_pixels, couleur="black", remplissage=depart_color)
    xmin_pix = min([p[0] for p in polygone_pixels])
    xmax_pix = max([p[0] for p in polygone_pixels])
    ymin_pix = min([p[1] for p in polygone_pixels])
    ymax_pix = max([p[1] for p in polygone_pixels])
    scale.database[numero_depart] = (xmin_pix, ymin_pix, xmax_pix,  ymax_pix)

def draw_clicked_polygone(clicked_polygone: int):
    # clicked_polygone - indice de polygone (0, 1, 2, ...)
    shape = all_shapes[clicked_polygone]
    record = records[clicked_polygone]
    depart_code = record[0]


    if depart_code in temp_departament:
        temp = temp_departament[depart_code]
        depart_color = temp_to_color(temp, tmin, tmax)
    else:
        depart_color = None

    pnts = shape.points
    prts = list(shape.parts) + [len(pnts)]


    xmin, ymin, xmax, ymax = shape.bbox
    dx = xmax - xmin
    dy = ymax - ymin


    preview_w = 100
    preview_h = 100
    margin = 30
    offset_x = scale.largeur - preview_w - margin
    offset_y = scale.hauteur - preview_h - margin

    sx = preview_w / dx
    sy = preview_h / dy
    s = min(sx, sy)

    draw_w = dx * s
    draw_h = dy * s

    center_x = offset_x + (preview_w - draw_w) / 2
    center_y = offset_y + (preview_h - draw_h) / 2


    for i in range(len(prts) - 1):
        segment = pnts[prts[i]:prts[i + 1]]
        segment_pixels = []
        for lon, lat in segment:
            x = (lon - xmin) * s + center_x
            # y инвертируем, чтобы север был сверху
            y = (ymax - lat) * s + center_y
            segment_pixels.append((x, y))
        polygone(segment_pixels, couleur="black", remplissage=depart_color, tag="polygone")


    texte(450, 700, f'departament: {record[3]}', taille=12, tag="depart")


    data = main2.trie()
    data_need = None
    for row in data:
        if row[1] == depart_code:
            data_need = row
            break

    if data_need:
        texte(450, 730, f'temperature moyenne: {data_need[5]}', taille=12, tag="temperature")
        texte(450, 760, f'date: {data_need[0]}', taille=12, tag="date")
    else:
        texte(450, 730, f'temperature moyenne: inconnue', taille=12, tag="temperature")
        texte(450, 760, f'date: {data[0][0]}', taille=12, tag="date")



for numero_depart, (shape, record) in enumerate(zip(all_shapes, records)):
    draw_shape(shape, record, numero_depart)




current_dx = 0 #pour bouger la carte avec deplace()
current_dy = 0

def se_deplacer(speed=10):
    global current_dx, current_dy
    dx = 0
    dy = 0
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
        deplace("gradient", -dx, -dy)
        deplace("temp_valeur", -dx, -dy)
        deplace("polygone", -dx, -dy)
        deplace("temperature", -dx, -dy)
        deplace("date", -dx, -dy)
        deplace("depart", -dx, -dy)
        current_dx += dx
        current_dy += dy


while True:
    se_deplacer()
    mise_a_jour()

    ev = donne_ev()
    if type_ev(ev) == 'Quitte':
        break

    if type_ev(ev) == "ClicGauche":
        # coordonnes de click en rendant comte carte bouge
        x_screen = abscisse(ev)
        y_screen = ordonnee(ev)

        # les convert dans coord basic
        x = x_screen - current_dx
        y = y_screen - current_dy

        clicked_polygone = None

        for numero_depart, (xmin_pix, ymin_pix, xmax_pix, ymax_pix) in scale.database.items():
            if xmin_pix <= x <= xmax_pix and ymin_pix <= y <= ymax_pix:
                clicked_polygone = numero_depart
                break

        if clicked_polygone is not None:
            efface("polygone")
            efface("temperature")
            efface("depart")
            efface("date")

            print(f'vous avez clique sur Polygone {clicked_polygone}')
            draw_clicked_polygone(clicked_polygone)

ferme_fenetre()
