import shapefile
from fltk import cree_fenetre, ferme_fenetre, attend_ev, polygone, mise_a_jour

path = "departements-20180101-shp/departements-20180101.shp"
sh_file = shapefile.Reader(path)


xmin, ymin, xmax, ymax = sh_file.bbox
#print(xmin, ymin, xmax, ymax)
all_shapes = sh_file.shapes()
#print(sh_file.shape(3).points) - all points of third depart
#print(sh_file.shape(3).parts)  - different parts of polygone

class GeoScale:
    def __init__(self, xmin, ymin, xmax, ymax, largeur, hauteur, aspect=True, zoom = 1.0):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.largeur = largeur
        self.hauteur = hauteur
        self.aspect = aspect

        dx = xmax - xmin
        dy = ymax - ymin #Диапазон между макс и мин координатoi

        sx = largeur / dx
        sy = hauteur / dy #Коэффицент масштабирования, чтобы карта не расплющивалась
        self.scale = min(sx, sy)*zoom

        map_larg = dx * self.scale
        map_haut = dy * self.scale
        self.offset_x = (largeur - map_larg) / 1.8
        self.offset_y = (hauteur - map_haut) - 250  #tabs for having a map in the middle

    def from_geo_to_pix(self, lon, lat):
        x = (lon - self.xmin) * self.scale + self.offset_x
        y = self.hauteur - ((lat - self.ymin) * self.scale + self.offset_y)
        return x, y

largeur = 800
hauteur = 800
scale = GeoScale(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, largeur=largeur, hauteur=hauteur,
                 zoom = 7.5)
cree_fenetre(largeur=largeur, hauteur=hauteur)
#x, y = scale.from_geo_to_pix(lon, lat)

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