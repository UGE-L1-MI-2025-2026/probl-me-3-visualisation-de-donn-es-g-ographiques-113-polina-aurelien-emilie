import shapefile
from fltk import cree_fenetre, ferme_fenetre, attend_ev, polygone, mise_a_jour
import math
def open_shapefile():
    path = "departements-20180101-shp/departements-20180101.shp"
    sh_file = shapefile.Reader(path)
    return sh_file

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

        map_larg = dx * self.scale
        map_haut = dy * self.scale
        self.offset_x = (largeur - map_larg) / 2
        print(self.offset_x)
        self.offset_y = (hauteur - map_haut)   #tabs for having a map in the middle

    def from_geo_to_pix(self, lon, lat):
        lon_rad = math.radians(lon)
        lat_rad = math.radians(lat)

        x = (lon_rad - self.xmin) + self.offset_x
        x*= self.scale 
        y =  math.log(math.tan(math.pi / 4 + lat_rad / 2))+self.offset_y
        y *= self.scale
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

mise_a_jour()
attend_ev()
ferme_fenetre()

