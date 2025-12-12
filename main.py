import shapefile
from fltk import *
import math
import main2

# Chargement shapefile 
def open_shapefile():
    path = "departements-20180101-shp/departements-20180101.shp"
    return shapefile.Reader(path)

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

all_shapes, records = trie_sh()

# Mercator 
def mercator_y(lat):
    lat_rad = math.radians(lat)
    return math.degrees(math.log(math.tan(math.pi/4 + lat_rad/2)))

def mercator_x(lon):
    return lon

# GeoScale 
class GeoScale:
    def __init__(self, xmin, ymin, xmax, ymax, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur
        self.Xmin = xmin
        self.Xmax = xmax
        self.Ymin = ymin
        self.Ymax = ymax

        dx = self.Xmax - self.Xmin
        dy = self.Ymax - self.Ymin
        self.scale = min(largeur/dx, hauteur/dy)
        map_larg = dx * self.scale
        map_haut = dy * self.scale
        self.offset_x = (largeur - map_larg)/2
        self.offset_y = (hauteur - map_haut)/2
        self.database = {}

    def from_geo_to_pix(self, lon, lat):
        X = lon
        Y = mercator_y(lat)
        x = (X - self.Xmin) * self.scale + self.offset_x
        y = (self.Ymax - Y) * self.scale + self.offset_y
        return x, y

# Calcul bbox 
min_lon = float('+inf')
max_lon = float('-inf')
min_lat = float('+inf')
max_lat = float('-inf')
for shape in all_shapes:
    for lon, lat in shape.points:
        min_lon = min(min_lon, lon)
        max_lon = max(max_lon, lon)
        min_lat = min(min_lat, lat)
        max_lat = max(max_lat, lat)

Xmin, Xmax = min_lon, max_lon
Ymin_merc, Ymax_merc = mercator_y(min_lat), mercator_y(max_lat)

scale = GeoScale(Xmin, Ymin_merc, Xmax, Ymax_merc, 800, 800)

#  Températures
def temp_par_departament():
    data = main2.trie()
    temp_departament = {}
    for i in range(1, len(data)):
        if data[i][5] == '':
            continue
        temp_departament[data[i][1]] = float(data[i][5])
    return temp_departament

def charger_toutes_temps():
    data = main2.trie() 
    temp_par_date = {}

    for i in range(len(data)): 
        date = data[i][0].strip()
        dep = data[i][1].strip()
        moy = data[i][5].strip()

        if moy == "":
            continue

        try:
            moy = float(moy) 
        except ValueError:
            continue

        if date not in temp_par_date:
            temp_par_date[date] = {}

        temp_par_date[date][dep] = moy

    return temp_par_date

def temp_to_color(temp, tmin, tmax):
    if tmax == tmin:
        norm = 0
    else:
        norm = (temp - tmin) / (tmax - tmin)
    r = int(255*norm)
    g = 0
    b = int(255 - 255*norm)
    return f'#{r:02x}{g:02x}{b:02x}'

temp_dates = charger_toutes_temps()
tmin_global = min(val for temps_par_dep in temp_dates.values() for val in temps_par_dep.values())
tmax_global = max(val for temps_par_dep in temp_dates.values() for val in temps_par_dep.values())
tmin = tmin_global
tmax = tmax_global
liste_dates = sorted(temp_dates.keys())
index_date = 0
temp_departament = temp_dates[liste_dates[index_date]]


#  Dessin 
def draw_shape(shape, record, numero_depart):
    depart_code = record[0]

    if depart_code in temp_departament:
        depart_color = temp_to_color(temp_departament[depart_code], tmin, tmax)
    else:
        depart_color = None

    pnts = shape.points
    prts = list(shape.parts) + [len(pnts)]

    polygone_pixels = []

    for i in range(len(prts)-1):
        segment = pnts[prts[i]:prts[i+1]]
        segment_pixels = [scale.from_geo_to_pix(lon, lat) for lon, lat in segment]

        polygone_pixels.extend(segment_pixels)

        polygone(segment_pixels, couleur="black", remplissage=depart_color, tag="carte")

    if not polygone_pixels:
        return

    xmin_pix = min(p[0] for p in polygone_pixels)
    xmax_pix = max(p[0] for p in polygone_pixels)
    ymin_pix = min(p[1] for p in polygone_pixels)
    ymax_pix = max(p[1] for p in polygone_pixels)

    scale.database[numero_depart] = (xmin_pix, ymin_pix, xmax_pix, ymax_pix)


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






"""def dessiner_carte():
    for shape, record in zip(all_shapes, records):
        draw_shape(shape, record, numero_depart)"""

def dessiner_legende():
    x, y = 770, 0
    texte(x - 10, y + 420, "(en °C)", tag="boutons", taille = 10)
    
    for i in range(-30, 40, 2):
        color = temp_to_color(i, -30, 40)
        rectangle(x, y, x + 30, y + 12, remplissage=color, tag="boutons")
        if i % 10 == 0:
            texte(x - 25, y, f"{i}°", tag="boutons", taille = 10)
        y += 12
     

def dessiner_boutons():
    rectangle(10, 10, 40, 40, remplissage="lightgray", tag="boutons")
    texte(22, 18, "<", taille=20, tag="boutons")
    rectangle(60, 10, 90, 40, remplissage="lightgray", tag="boutons")
    texte(72, 18, ">", taille=20, tag="boutons")

    texte(120, 15, liste_dates[index_date], taille=16, tag="boutons")

def dessiner_champ_saisie():
    FENETRE_LARGEUR = 800 
    x_start = (FENETRE_LARGEUR / 2) - (100 / 2) 
    y_start = 760 
    x_end = x_start + 100
    y_end = y_start + 30
    
    rectangle(x_start, y_start, x_end, y_end, remplissage="white", couleur="black", tag="input_date")
    global date_saisie_courante
    texte(x_start, y_start - 15, "Saisir date (AAAA-MM-JJ) + Entrée", ancrage='nw', taille=10, tag="input_date_aide")
    texte_a_afficher = date_saisie_courante if date_saisie_courante else "AAAA-MM-JJ"
    texte(x_start + 5, y_start + 5, texte_a_afficher, ancrage='nw', couleur="gray", taille=10 if not date_saisie_courante else "black", tag="input_date_texte")


date_saisie_courante = ""

#  Changer date 
def set_date(i):
    global temp_departament, index_date
    index_date = i
    temp_departament = temp_dates[liste_dates[index_date]]
    efface("carte")
    efface("boutons")  
    dessiner_legende()
    dessiner_boutons()

cree_fenetre(scale.largeur, scale.hauteur)
set_date(0)
dessiner_champ_saisie()


for numero_depart, (shape, record) in enumerate(zip(all_shapes, records)):
    draw_shape(shape, record, numero_depart)


current_dx = 0 #pour bouger la carte avec deplace()
current_dy = 0

#  Déplacement 
def se_deplacer(speed=10):
    global current_dx, current_dy
    dx = dy = 0

    if touche_pressee("Left"):  dx += speed
    if touche_pressee("Right"): dx -= speed
    if touche_pressee("Up"):    dy += speed
    if touche_pressee("Down"):  dy -= speed

    if dx != 0 or dy != 0:
        current_dx += dx
        current_dy += dy
        deplace("carte", dx, dy)

def se_deplacer(speed=10):
    deplacee = False

    if touche_pressee("Left"):
        scale.move_x += speed
        deplacee = True
    if touche_pressee("Right"):
        scale.move_x -= speed
        deplacee = True
    if touche_pressee("Up"):
        scale.move_y += speed
        deplacee = True
    if touche_pressee("Down"):
        scale.move_y -= speed
        deplacee = True

    return deplacee


def zoomer():
    ZOOM_IN = 1.1
    ZOOM_OUT = 1 / 1.1
    
    zoomee = False

    if touche_pressee("z"):     
        scale.scale *= ZOOM_IN
        zoomee = True

    if touche_pressee("d"):     
        scale.scale *= ZOOM_OUT
        zoomee = True

    return zoomee



    
while True:
    ev = donne_ev()
    while ev is not None:

        if type_ev(ev) == 'Quitte':
            ferme_fenetre()
            exit()

        elif type_ev(ev) == 'Touche':
            touche = touche(ev)
            if not isinstance(touche, str):
                ev = donne_ev()
                continue
            if touche == 'Return':
                try_date = date_saisie_courante
                if try_date in temp_dates:
                    new_index = liste_dates.index(try_date)
                    set_date(new_index)
                    date_saisie_courante = ""
                else:
                    print(f"Erreur : Date '{try_date}' non trouvée ou format invalide.")
                    date_saisie_courante = "Erreur!"

            elif touche == 'BackSpace':
                date_saisie_courante = date_saisie_courante[:-1]
            elif touche in touche.isdigit():
                if len(date_saisie_courante) < 10:
                    date_saisie_courante += touche
                else: 
                    char_a_ajouter = touche
                
                if char_a_ajouter is not None and len(date_saisie_courante) < 10:
                    date_saisie_courante += char_a_ajouter
        elif type_ev(ev) == 'ClicGauche':
            x = abscisse(ev)
            y = ordonnee(ev)
            x_screen = abscisse(ev)
            y_screen = ordonnee(ev)
            x2 = x_screen - current_dx
            y2 = y_screen - current_dy
            clicked_polygone = None

            for numero_depart, (xmin_pix, ymin_pix, xmax_pix, ymax_pix) in scale.database.items():
                if xmin_pix <= x2 <= xmax_pix and ymin_pix <= y2 <= ymax_pix:
                    clicked_polygone = numero_depart
                    break


            if clicked_polygone is not None:
                efface("polygone")
                efface("temperature")
                efface("depart")
                efface("date")

                print(f'vous avez clique sur Polygone {clicked_polygone}')
                draw_clicked_polygone(clicked_polygone)


            if 10 <= x <= 40 and 10 <= y <= 40:
                if index_date > 0:
                    set_date(index_date - 1)

            # Bouton >
            if 60 <= x <= 90 and 10 <= y <= 40:
                if index_date < len(liste_dates) - 1:
                    set_date(index_date + 1)
            


        ev = donne_ev()

    # Touche maintenues → déplacement & zoom
    deplacee = deplacer()
    zoomee = zoomer()

    # Si la carte doit être mise à jour
    if deplacee or zoomee:
        efface("carte")
        dessiner_carte()


    mise_a_jour()

ev = donne_ev()
