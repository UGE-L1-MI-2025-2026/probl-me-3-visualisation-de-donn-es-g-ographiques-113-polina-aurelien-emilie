import shapefile
from fltk import *
import math
import main2


def open_shapefile():
    path = "departements-20180101-shp/departements-20180101.shp"
    return shapefile.Reader(path)

sh_file = open_shapefile()

def trie_sh():
    resultat_shapes = []
    resultat_records = []
    DROM = {'971', '972', '973', '974', '976'}

    records = sh_file.records()
    shapes = sh_file.shapes()

    for rec, shp in zip(records, shapes):
        code_dep = rec[0]
        if code_dep not in DROM:
            resultat_shapes.append(shp)
            resultat_records.append(rec)

    return resultat_shapes, resultat_records

all_shapes, records = trie_sh()


def mercator_y(lat):
    lat_rad = math.radians(lat)
    return math.degrees(math.log(math.tan(math.pi/4 + lat_rad/2)))

def mercator_x(lon):
    return lon


class GeoScale:
    def __init__(self, xmin, ymin, xmax, ymax, largeur, hauteur, database=None):
        self.largeur = largeur
        self.hauteur = hauteur
        self.Xmin = xmin
        self.Xmax = xmax
        self.Ymin = ymin
        self.Ymax = ymax
        self.database = database if database is not None else {}

        dx = self.Xmax - self.Xmin
        dy = self.Ymax - self.Ymin

        self.scale = min(largeur / dx, hauteur / dy)

        map_larg = dx * self.scale
        map_haut = dy * self.scale
        self.offset_x = (largeur - map_larg) / 2
        self.offset_y = (hauteur - map_haut) / 2

    def from_geo_to_pix(self, lon, lat):
        X = mercator_x(lon)
        Y = mercator_y(lat)
        x = (X - self.Xmin) * self.scale + self.offset_x
        y = (self.Ymax - Y) * self.scale + self.offset_y  # inversion Y
        return x, y

min_lon = float('+inf')
max_lon = float('-inf')
min_ymerc = float('+inf')
max_ymerc = float('-inf')

for shp in all_shapes:
    for lon, lat in shp.points:
        min_lon = min(min_lon, lon)
        max_lon = max(max_lon, lon)
        ymerc = mercator_y(lat)
        min_ymerc = min(min_ymerc, ymerc)
        max_ymerc = max(max_ymerc, ymerc)

scale = GeoScale(min_lon, min_ymerc, max_lon, max_ymerc, 800, 800, database={})


def charger_toutes_temps():
    data = main2.trie()
    temp_par_date = {}

    for row in data:
        date = row[0].strip()
        dep = row[1].strip()
        moy = row[5].strip()

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
    norm = max(0, min(1, norm))
    r = int(255 * norm)
    g = 0
    b = int(255 - 255 * norm)
    return f'#{r:02x}{g:02x}{b:02x}'

temp_dates = charger_toutes_temps()
liste_dates = sorted(temp_dates.keys())
index_date = 0
temp_departament = temp_dates[liste_dates[index_date]]

tmin = min(v for d in temp_dates.values() for v in d.values())
tmax = max(v for d in temp_dates.values() for v in d.values())


data_all = main2.trie()


def draw_shape(shape, record, numero_depart):
    depart_code = record[0]
    if depart_code in temp_departament:
        depart_color = temp_to_color(temp_departament[depart_code], tmin, tmax)
    else:
        depart_color = None

    pnts = shape.points
    prts = list(shape.parts) + [len(pnts)]

    polygone_pixels = []

    for i in range(len(prts) - 1):
        segment = pnts[prts[i]:prts[i+1]]
        segment_pixels = []
        for lon, lat in segment:
            coords = scale.from_geo_to_pix(lon, lat)
            segment_pixels.append(coords)
            polygone_pixels.append(coords)

        polygone(segment_pixels, couleur="black", remplissage=depart_color, tag="carte")

    # bbox en pixels (pour click)
    xmin_pix = min(p[0] for p in polygone_pixels)
    xmax_pix = max(p[0] for p in polygone_pixels)
    ymin_pix = min(p[1] for p in polygone_pixels)
    ymax_pix = max(p[1] for p in polygone_pixels)
    scale.database[numero_depart] = (xmin_pix, ymin_pix, xmax_pix, ymax_pix)

def dessiner_carte():
    scale.database = {}
    for numero_depart, (shape, record) in enumerate(zip(all_shapes, records)):
        draw_shape(shape, record, numero_depart)


def dessiner_legende():
    x, y = 770, 0
    for i in range(-30, 40, 2):
        color = temp_to_color(i, -30, 40)
        rectangle(x, y, x+30, y+12, remplissage=color, tag="ui")
        if i % 10 == 0:
            texte(x-35, y, f"{i}°", tag="ui")
        y += 12

def dessiner_boutons():
    rectangle(10, 10, 40, 40, remplissage="lightgray", tag="ui")
    texte(22, 18, "<", taille=20, tag="ui")
    rectangle(60, 10, 90, 40, remplissage="lightgray", tag="ui")
    texte(72, 18, ">", taille=20, tag="ui")
    texte(120, 15, liste_dates[index_date], taille=16, tag="ui")

date_saisie_courante = ""

def dessiner_champ_saisie():
    FENETRE_LARGEUR = 800
    x_start = (FENETRE_LARGEUR / 2) - (100 / 2)
    y_start = 760
    x_end = x_start + 100
    y_end = y_start + 30

    rectangle(x_start, y_start, x_end, y_end, remplissage="white", couleur="black", tag="ui")

    texte(x_start, y_start - 15, "Saisir date (AAAA-MM-JJ) + Entrée",
          ancrage='nw', taille=10, tag="ui")

    texte_a_afficher = date_saisie_courante if date_saisie_courante else "AAAA-MM-JJ"
    if date_saisie_courante:
        texte(x_start + 5, y_start + 5, texte_a_afficher, ancrage='nw', taille=10, tag="ui")
    else:
        texte(x_start + 5, y_start + 5, texte_a_afficher, ancrage='nw', couleur="gray", taille=10, tag="ui")


def draw_clicked_polygone(clicked_polygone: int):
    shape = all_shapes[clicked_polygone]
    record = records[clicked_polygone]
    depart_code = record[0]

    if depart_code in temp_departament:
        depart_color = temp_to_color(temp_departament[depart_code], tmin, tmax)
    else:
        depart_color = None

    pnts = shape.points
    prts = list(shape.parts) + [len(pnts)]

    # bbox geo
    xmin, ymin, xmax, ymax = shape.bbox
    dx = xmax - xmin
    dy = ymax - ymin

    preview_w = 120
    preview_h = 120
    margin = 30
    offset_x = scale.largeur - preview_w - margin
    offset_y = scale.hauteur - preview_h - margin

    sx = preview_w / dx if dx != 0 else 1
    sy = preview_h / dy if dy != 0 else 1
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
            y = (ymax - lat) * s + center_y  # inversion y simple
            segment_pixels.append((x, y))
        polygone(segment_pixels, couleur="black", remplissage=depart_color, tag="info")

    texte(450, 700, f"departement: {record[3]}", taille=12, tag="info")

    # trouve une ligne data pour ce dep + date courante si possible
    date_cur = liste_dates[index_date]
    data_need = None
    for row in data_all:
        if row[1].strip() == depart_code and row[0].strip() == date_cur:
            data_need = row
            break
    if data_need is None:
        for row in data_all:
            if row[1].strip() == depart_code:
                data_need = row
                break

    if data_need:
        texte(450, 730, f"temperature moyenne: {data_need[5]}", taille=12, tag="info")
        texte(450, 760, f"date: {data_need[0]}", taille=12, tag="info")
    else:
        texte(450, 730, "temperature moyenne: inconnue", taille=12, tag="info")
        texte(450, 760, f"date: {date_cur}", taille=12, tag="info")


def set_date(i):
    global temp_departament, index_date
    index_date = i
    temp_departament = temp_dates[liste_dates[index_date]]

    efface("carte")
    dessiner_carte()

    efface("ui")
    dessiner_legende()
    dessiner_boutons()
    dessiner_champ_saisie()

    efface("info")

current_dx = 0
current_dy = 0

def se_deplacer(speed=10):
    global current_dx, current_dy
    dx = dy = 0
    if touche_pressee("Left"):  dx += speed
    if touche_pressee("Right"): dx -= speed
    if touche_pressee("Up"):    dy += speed
    if touche_pressee("Down"):  dy -= speed
    if dx != 0 or dy != 0:
        deplace("carte", dx, dy)  # только карта
        current_dx += dx
        current_dy += dy


cree_fenetre(scale.largeur, scale.hauteur)
set_date(0)

CARACTERES_AZERTY_CHIFFRES = "0123456789-&é\"'(-è_çà)="
mapping_azerty = {'&': '1', 'é': '2', '"': '3', "'": '4', '(': '5', '-': '6',
                  'è': '7', '_': '8', 'ç': '9', 'à': '0', '=': '-'}

while True:
    se_deplacer()
    mise_a_jour()

    ev = donne_ev()
    while ev is not None:
        if type_ev(ev) == 'Quitte':
            ferme_fenetre()
            exit()

        elif type_ev(ev) == 'Touche':
            touche = touche_pressee(ev)
            if not isinstance(touche, str):
                ev = donne_ev()
                continue

            global date_saisie_courante

            if touche == 'Return':
                try_date = date_saisie_courante
                if try_date in temp_dates:
                    new_index = liste_dates.index(try_date)
                    date_saisie_courante = ""
                    set_date(new_index)
                else:
                    print(f"Erreur : Date '{try_date}' non trouvée.")
                    date_saisie_courante = "Erreur!"
                    efface("ui")
                    dessiner_legende()
                    dessiner_boutons()
                    dessiner_champ_saisie()

            elif touche == 'BackSpace':
                date_saisie_courante = date_saisie_courante[:-1]
                efface("ui")
                dessiner_legende()
                dessiner_boutons()
                dessiner_champ_saisie()

            elif touche in CARACTERES_AZERTY_CHIFFRES or touche.isdigit() or touche == '-':
                if touche in mapping_azerty:
                    char_a_ajouter = mapping_azerty[touche]
                else:
                    char_a_ajouter = touche

                if len(date_saisie_courante) < 10:
                    date_saisie_courante += char_a_ajouter
                    efface("ui")
                    dessiner_legende()
                    dessiner_boutons()
                    dessiner_champ_saisie()

        elif type_ev(ev) == 'ClicGauche':
            x_screen = abscisse(ev)
            y_screen = ordonnee(ev)

            # boutons UI (fixes)
            if 10 <= x_screen <= 40 and 10 <= y_screen <= 40:
                if index_date > 0:
                    date_saisie_courante = ""
                    set_date(index_date - 1)

            elif 60 <= x_screen <= 90 and 10 <= y_screen <= 40:
                if index_date < len(liste_dates) - 1:
                    date_saisie_courante = ""
                    set_date(index_date + 1)

            else:
                # clic sur carte: on remet dans repère "carte" (carte bougée)
                x = x_screen - current_dx
                y = y_screen - current_dy

                clicked_polygone = None
                for numero_depart, (xmin_pix, ymin_pix, xmax_pix, ymax_pix) in scale.database.items():
                    if xmin_pix <= x <= xmax_pix and ymin_pix <= y <= ymax_pix:
                        clicked_polygone = numero_depart
                        break

                if clicked_polygone is not None:
                    efface("info")
                    print(f"vous avez clique sur Polygone {clicked_polygone}")
                    draw_clicked_polygone(clicked_polygone)

        ev = donne_ev()

ferme_fenetre()