import subprocess
import sys
import tkinter as tk
from collections import deque
from functools import wraps
from math import ceil
from os import system
from pathlib import Path
from time import sleep, time
from tkinter import PhotoImage
from tkinter.font import Font
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Deque,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

try:
    # noinspection PyUnresolvedReferences
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
    print("Bibliothèque PIL chargée.", file=sys.stderr)
    PILImage = Image.Image
    __pil_cache: Dict[Tuple[Path, Optional[int], Optional[int], int], PILImage] = {}
except ImportError as e:
    print("Bibliothèque PIL non disponible. "
          "Installer pillow pour plus de fonctionnalités", file=sys.stderr)
    PIL_AVAILABLE = False

if TYPE_CHECKING:
    from typing_extensions import Literal, TypedDict

    Anchor = Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"]
    TkEvent = tk.Event[tk.BaseWidget]
else:
    Anchor = str
    TkEvent = tk.Event

FltkEvent = Tuple[str, Optional[TkEvent]]


__all__ = [
    # gestion de fenêtre
    "cree_fenetre",
    "ferme_fenetre",
    "redimensionne_fenetre",
    "mise_a_jour",
    # dessiner
    "arc",
    "cercle",
    "fleche",
    "image",
    "ligne",
    "ovale",
    "point",
    "polygone",
    "rectangle",
    "texte",
    # modif et info objets
    "efface_tout",
    "efface",
    "modifie",
    "rotation_image",
    "redimensionne_image",
    "deplace",
    "couleur",
    "remplissage",
    "taille_texte",
    "type_objet",
    "recuperer_tags",
    # utilitaires
    "attente",
    "capture_ecran",
    "touche_pressee",
    "repere",
    # événements
    "donne_ev",
    "attend_ev",
    "attend_clic_gauche",
    "attend_fermeture",
    "type_ev",
    "abscisse",
    "ordonnee",
    "touche",
    # info fenetre
    "abscisse_souris",
    "ordonnee_souris",
    "hauteur_fenetre",
    "largeur_fenetre",
    "liste_objets_survoles",
    "objet_survole",
    "est_objet_survole",
]

class CustomCanvas:
    """
    Classe qui encapsule tous les objets tkinter nécessaires à la création
    d'un canevas.
    """

    _on_osx = sys.platform.startswith("darwin")

    _ev_mapping = {
        "ClicGauche": "<Button-1>",
        "ClicMilieu": "<Button-2>",
        "ClicDroit": "<Button-2>" if _on_osx else "<Button-3>",
        "Deplacement": "<Motion>",
        "Touche": "<Key>",
        "Redimension": "<Configure>",
    }

    _default_ev = ["ClicGauche", "ClicDroit", "Touche"]

    def __init__(
            self,
            width: int,
            height: int,
            refresh_rate: int = 100,
            events: Optional[List[str]] = None,
            resizing: bool = False
    ) -> None:
        # width and height of the canvas
        self.width = width
        self.height = height
        self.interval = 1 / refresh_rate

        # root Tk object
        self.root = tk.Tk()

        # canvas attached to the root object
        self.canvas = tk.Canvas(
            self.root, width=width, height=height, highlightthickness=0
        )

        # adding the canvas to the root window and giving it focus
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.root.resizable(width=resizing, height=resizing)
        self.canvas.focus_set()
        self.first_resize = True

        # binding events
        self.ev_queue: Deque[FltkEvent] = deque()
        self.pressed_keys: Set[str] = set()
        self.events = CustomCanvas._default_ev if events is None else events
        self.bind_events()

        # update for the first time
        self.last_update = time()
        self.root.update()

        if CustomCanvas._on_osx:
            system(
                """/usr/bin/osascript -e 'tell app "Finder" \
                   to set frontmost of process "Python" to true' """
            )

    def update(self) -> None:
        t = time()
        self.root.update()
        sleep(max(0.0, self.interval - (t - self.last_update)))
        self.last_update = time()

    def resize(self, width: int, height: int) -> None:
        self.root.geometry(f"{int(width)}x{int(height)}")

    def bind_events(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self.event_quit)
        self.canvas.bind("<Configure>", self.event_resize)
        self.canvas.bind("<KeyPress>", self.register_key)
        self.canvas.bind("<KeyRelease>", self.release_key)
        for name in self.events:
            self.bind_event(name)

    # noinspection PyUnresolvedReferences
    def register_key(self, ev: TkEvent) -> None:
        self.pressed_keys.add(ev.keysym)

    # noinspection PyUnresolvedReferences
    def release_key(self, ev: TkEvent) -> None:
        if ev.keysym in self.pressed_keys:
            self.pressed_keys.remove(ev.keysym)

    def event_quit(self) -> None:
        self.ev_queue.append(("Quitte", None))

    # noinspection PyUnresolvedReferences
    def event_resize(self, event: TkEvent) -> None:
        if event.widget.widgetName == "canvas":
            if self.width != event.width or self.height != event.height:
                self.width, self.height = event.width, event.height
                if not self.ev_queue or self.ev_queue[-1][0] != "Redimension":
                    self.ev_queue.append(("Redimension", event))

    def bind_event(self, name: str) -> None:
        e_type = CustomCanvas._ev_mapping.get(name, name)

        def handler(event: TkEvent, _name: str = name) -> None:
            self.ev_queue.append((_name, event))

        self.canvas.bind(e_type, handler, "+")

    def unbind_event(self, name: str) -> None:
        e_type = CustomCanvas._ev_mapping.get(name, name)
        self.canvas.unbind(e_type)


__canevas: Optional[CustomCanvas] = None
__img_cache: Dict[Tuple[Path, Optional[int], Optional[int], int], PhotoImage] = {}

if TYPE_CHECKING:
    StatDictValue = TypedDict('StatDictValue', {"file": str,
                                                "height": int,
                                                "width": int,
                                                "angle": Union[int, float],
                                                "photoimage": PhotoImage})
else:
    StatDictValue = dict

__img_stats: Dict[int, StatDictValue] = {}

__trans_object_type = {
    "arc": "arc",
    "image": "image",
    "line": "ligne",
    "oval": "ovale",
    "polygon": "polygone",
    "rectangle": "rectangle",
    "text": "texte",
}

__trans_options = {
    "remplissage": "fill",
    "couleur": "outline",
    "epaisseur": "width",
}


#############################################################################
# Exceptions
#############################################################################


class TypeEvenementNonValide(Exception):
    pass


class FenetreNonCree(Exception):
    pass


class FenetreDejaCree(Exception):
    pass


Ret = TypeVar("Ret")


def _fenetre_creee(func: Callable[..., Ret]) -> Callable[..., Ret]:
    @wraps(func)
    def new_func(*args: Any, **kwargs: Any) -> Ret:
        if __canevas is None:
            raise FenetreNonCree(
                'La fenêtre n\'a pas été crée avec la fonction "cree_fenetre".'
            )
        return func(*args, **kwargs)

    return new_func


#############################################################################
# Initialisation, mise à jour et fermeture
#############################################################################


def cree_fenetre(
        largeur: int, hauteur: int, frequence: int = 100,
        redimension: bool = False, affiche_repere : bool = False
) -> None:
    """
    Crée une fenêtre de dimensions ``largeur`` x ``hauteur`` pixels.
    :rtype:
    """
    global __canevas
    if __canevas is not None:
        raise FenetreDejaCree(
            'La fenêtre a déjà été crée avec la fonction "cree_fenetre".'
        )
    __canevas = CustomCanvas(largeur, hauteur, frequence, resizing=redimension)
    if affiche_repere:
        repere()


@_fenetre_creee
def ferme_fenetre() -> None:
    """
    Détruit la fenêtre.
    """
    global __canevas
    assert __canevas is not None
    __canevas.root.destroy()
    __canevas = None
    __img_cache.clear()
    __img_stats.clear()


@_fenetre_creee
def redimensionne_fenetre(largeur: int, hauteur: int) -> None:
    """
    Fixe les dimensions de la fenêtre à (``hauteur`` x ``largeur``) pixels.

    Le contenu du canevas n'est pas automatiquement mis à l'échelle et doit
    être redessiné si nécessaire.
    """
    assert __canevas is not None
    __canevas.resize(width=largeur, height=hauteur)


@_fenetre_creee
def mise_a_jour() -> None:
    """
    Met à jour la fenêtre. Les dessins ne sont affichés qu'après
    l'appel à cette fonction.
    """
    assert __canevas is not None
    __canevas.update()


#############################################################################
# Fonctions de dessin
#############################################################################


# Formes géométriques


@_fenetre_creee
def ligne(
        ax: float,
        ay: float,
        bx: float,
        by: float,
        couleur: str = "black",
        epaisseur: float = 1,
        tag: str = "",
) -> int:
    """
    Trace un segment reliant le point ``(ax, ay)`` au point ``(bx, by)``.

    :param float ax: abscisse du premier point
    :param float ay: ordonnée du premier point
    :param float bx: abscisse du second point
    :param float by: ordonnée du second point
    :param str couleur: couleur de trait (défaut 'black')
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    return __canevas.canvas.create_line(
        ax, ay, bx, by, fill=couleur, width=epaisseur, tags=tag
    )


@_fenetre_creee
def fleche(
        ax: float,
        ay: float,
        bx: float,
        by: float,
        couleur: str = "black",
        epaisseur: float = 1,
        tag: str = "",
) -> int:
    """
    Trace une flèche du point ``(ax, ay)`` au point ``(bx, by)``.

    :param float ax: abscisse du premier point
    :param float ay: ordonnée du premier point
    :param float bx: abscisse du second point
    :param float by: ordonnée du second point
    :param str couleur: couleur de trait (défaut 'black')
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    x, y = (bx - ax, by - ay)
    n = (x ** 2 + y ** 2) ** 0.5
    x, y = x / n, y / n
    points = [
        bx,
        by,
        bx - x * 5 - 2 * y,
        by - 5 * y + 2 * x,
        bx - x * 5 + 2 * y,
        by - 5 * y - 2 * x,
    ]
    assert __canevas is not None
    return __canevas.canvas.create_polygon(
        points, fill=couleur, outline=couleur, width=epaisseur, tags=tag
    )


@_fenetre_creee
def polygone(
        points: List[float],
        couleur: str = "black",
        remplissage: str = "",
        epaisseur: float = 1,
        tag: str = "",
) -> int:
    """
    Trace un polygone dont la liste de points est fournie.

    :param list points: liste de couples (abscisse, ordonnee) de points
    :param str couleur: couleur de trait (défaut 'black')
    :param str remplissage: couleur de fond (défaut transparent)
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    if epaisseur == 0:
        couleur = ""
    return __canevas.canvas.create_polygon(
        points, fill=remplissage, outline=couleur, width=epaisseur, tags=tag
    )


@_fenetre_creee
def rectangle(
        ax: float,
        ay: float,
        bx: float,
        by: float,
        couleur: str = "black",
        remplissage: str = "",
        epaisseur: float = 1,
        tag: str = "",
) -> int:
    """
    Trace un rectangle noir ayant les point ``(ax, ay)`` et ``(bx, by)``
    comme coins opposés.

    :param float ax: abscisse du premier coin
    :param float ay: ordonnée du premier coin
    :param float bx: abscisse du second coin
    :param float by: ordonnée du second coin
    :param str couleur: couleur de trait (défaut 'black')
    :param str remplissage: couleur de fond (défaut transparent)
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    return __canevas.canvas.create_rectangle(
        ax, ay, bx, by,
        outline=couleur, fill=remplissage, width=epaisseur, tags=tag
    )


@_fenetre_creee
def cercle(
        x: float,
        y: float,
        r: float,
        couleur: str = "black",
        remplissage: str = "",
        epaisseur: float = 1,
        tag: str = "",
) -> int:
    """
    Trace un cercle de centre ``(x, y)`` et de rayon ``r`` en noir.

    :param float x: abscisse du centre
    :param float y: ordonnée du centre
    :param float r: rayon
    :param str couleur: couleur de trait (défaut 'black')
    :param str remplissage: couleur de fond (défaut transparent)
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    return __canevas.canvas.create_oval(
        x - r,
        y - r,
        x + r,
        y + r,
        outline=couleur,
        fill=remplissage,
        width=epaisseur,
        tags=tag,
    )


@_fenetre_creee
def ovale(
        ax: float,
        ay: float,
        bx : float,
        by : float,
        couleur: str = "black",
        remplissage: str = "",
        epaisseur: float = 1,
        tag: str = "",
) -> int:
    """
    Trace un ovale compris dans le rectangle de coins ``(ax, ay)`` et ``(bx, by)``.

    :param float ax: abscisse du premier coin
    :param float ay: ordonnée du premier coin
    :param float bx: abscisse du second coin
    :param float by: ordonnée du second coin
    :param str couleur: couleur de trait (défaut 'black')
    :param str remplissage: couleur de fond (défaut transparent)
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    return __canevas.canvas.create_oval(
        ax, ay, bx, by,
        outline=couleur,
        fill=remplissage,
        width=epaisseur,
        tags=tag,
    )


@_fenetre_creee
def arc(
        x: float,
        y: float,
        r: float,
        ouverture: float = 90,
        depart: float = 0,
        couleur: str = "black",
        remplissage: str = "",
        epaisseur: float = 1,
        tag: str = "",
) -> int:
    """
    Trace un arc de cercle de centre ``(x, y)``, de rayon ``r`` et
    d'angle d'ouverture ``ouverture`` (défaut : 90 degrés, dans le sens
    contraire des aiguilles d'une montre) depuis l'angle initial ``depart``
    (défaut : direction 'est').

    :param float x: abscisse du centre
    :param float y: ordonnée du centre
    :param float r: rayon
    :param float ouverture: abscisse du centre
    :param float depart: ordonnée du centre
    :param str couleur: couleur de trait (défaut 'black')
    :param str remplissage: couleur de fond (défaut transparent)
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    return __canevas.canvas.create_arc(
        x - r,
        y - r,
        x + r,
        y + r,
        extent=ouverture,
        start=depart,
        style=tk.ARC,
        outline=couleur,
        fill=remplissage,
        width=epaisseur,
        tags=tag,
    )


@_fenetre_creee
def point(
        x: float, y: float,
        couleur: str = "black", epaisseur: float = 1,
        tag: str = ""
) -> int:
    """
    Trace un point aux coordonnées ``(x, y)`` en noir.

    :param float x: abscisse
    :param float y: ordonnée
    :param str couleur: couleur du point (défaut 'black')
    :param float epaisseur: épaisseur de trait en pixels (défaut 1)
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    return cercle(x, y, epaisseur,
                  couleur=couleur, remplissage=couleur, tag=tag)


# Image
@_fenetre_creee
def image(
        x: float,
        y: float,
        fichier: str,
        largeur: Optional[int] = None,
        hauteur: Optional[int] = None,
        ancrage: Anchor = "center",
        tag: str = "",
        angle: int = 0
) -> int:
    """
    Affiche l'image contenue dans ``fichier`` avec ``(x, y)`` comme centre. Les
    valeurs possibles du point d'ancrage sont ``'center'``, ``'nw'``,
    etc. Les arguments optionnels ``largeur`` et ``hauteur`` permettent de
    spécifier des dimensions maximales pour l'image (sans changement de
    proportions).

    :param float x: abscisse du point d'ancrage
    :param float y: ordonnée du point d'ancrage
    :param str fichier: nom du fichier contenant l'image
    :param largeur: largeur de l'image
    :param hauteur: hauteur de l'image
    :param ancrage: position du point d'ancrage par rapport à l'image
    :param str tag: étiquette d'objet (défaut : pas d'étiquette)
    :param int angle: angle de rotation de l'image (défaut : 0)
    :return: identificateur d'objet
    """
    assert __canevas is not None
    if PIL_AVAILABLE:
        tk_image = _load_pil_image(fichier, hauteur, largeur, angle)
    else:
        tk_image = _load_tk_image(fichier, hauteur, largeur)
    img_object = __canevas.canvas.create_image(
        x, y, anchor=ancrage, image=tk_image, tags=tag)
    __img_stats[img_object] = {"file": fichier,
                               "height": tk_image.height(),
                               "width": tk_image.width(),
                               "angle": angle,
                               "photoimage": tk_image}
    return img_object


def _load_tk_image(fichier: str,
                   hauteur: Optional[int] = None,
                   largeur: Optional[int] = None,
                   angle: int = 0) -> PhotoImage:
    if angle != 0:
        print("Image rotation not implemented "
              "(install pillow for more features)", file=sys.stderr)
    chemin = Path(fichier)
    if (chemin, None, None, 0) in __img_cache:
        ph_image = __img_cache[(chemin, None, None, 0)]
    else:
        ph_image = PhotoImage(file=fichier)
        __img_cache[(chemin, None, None, 0)] = ph_image
    largeur_o = ph_image.width()
    hauteur_o = ph_image.height()
    if largeur is None:
        largeur = largeur_o
    if hauteur is None:
        hauteur = hauteur_o
    zoom_l = max(1, round(largeur / largeur_o))
    zoom_h = max(1, round(hauteur / hauteur_o))
    red_l = max(1, round(largeur_o / largeur))
    red_h = max(1, round(hauteur_o / hauteur))
    largeur_reelle = ceil(largeur_o * zoom_l / red_l)
    hauteur_reelle = ceil(hauteur_o * zoom_h / red_h)
    if largeur_reelle != largeur or hauteur_reelle != hauteur:
        print(f"Image with requested size {largeur}x{hauteur} "
              f"displayed with actual size {largeur_reelle}x{hauteur_reelle}",
              file=sys.stderr)
        print("(install pillow for fine-grained image resizing)", file=sys.stderr)
    if (chemin, largeur_reelle, hauteur_reelle, 0) in __img_cache:
        return __img_cache[(chemin, largeur_reelle, hauteur_reelle, 0)]
    ph_image = ph_image.zoom(zoom_l, zoom_h)
    ph_image = ph_image.subsample(red_l, red_h)
    __img_cache[(chemin, ph_image.width(), ph_image.height(), 0)] = ph_image
    return ph_image


def _load_pil_image(fichier: str,
                    hauteur: Optional[int] = None,
                    largeur: Optional[int] = None,
                    angle: int = 0) -> PhotoImage:
    assert PIL_AVAILABLE
    chemin = Path(fichier)
    angle %= 360
    if (chemin, largeur, hauteur, angle) in __img_cache:
        return __img_cache[(chemin, largeur, hauteur, angle)]
    if (chemin, largeur, hauteur, 0) in __pil_cache:
        img = __pil_cache[(chemin, largeur, hauteur, 0)]
    elif (chemin, None, None, 0) in __pil_cache:
        img = __pil_cache[(chemin, None, None, 0)]
    else:
        img = Image.open(fichier)
        __pil_cache[(chemin, None, None, 0)] = img
    if largeur is None:
        largeur = img.width
    if hauteur is None:
        hauteur = img.height
    if largeur != img.width or hauteur != img.height:
        img = img.resize((largeur, hauteur))
        __pil_cache[(chemin, largeur, hauteur, 0)] = img
    if angle != 0:
        img = img.rotate(angle)
        __pil_cache[(chemin, largeur, hauteur, angle)] = img
    ph_image = ImageTk.PhotoImage(img)
    __img_cache[(chemin, largeur, hauteur, angle)] = ph_image  # type:ignore
    return ph_image  # type:ignore


@_fenetre_creee
def _get_anchor_coords(object_or_tag: Union[int, str]) -> Tuple[int, int, str]:
    assert __canevas is not None
    x1, y1, x2, y2 = __canevas.canvas.bbox(object_or_tag)
    xc = (x1 + x2) // 2
    yc = (y1 + y2) // 2
    anchor = __canevas.canvas.itemcget(object_or_tag, "anchor")
    if anchor[0] == 'n':
        y = y1
    elif anchor[0] == 's':
        y = y2
    else:
        y = yc
    if anchor[-1] == 'w':
        x = x1
    elif anchor[-1] == 'e':
        x = x2
    else:
        x = xc
    return x, y, anchor


@_fenetre_creee
def _locate_object(object_or_tag: Union[int, str]) -> int:
    assert __canevas is not None
    objects = __canevas.canvas.find_withtag(object_or_tag)
    if objects == () or objects[0] not in __img_stats:
        raise ValueError(f"Objet {object_or_tag} inconnu.")
    return objects[0]


@_fenetre_creee
def hauteur_image(image_id: int) -> int:
    return __img_stats[image_id]['height']


@_fenetre_creee
def largeur_image(image_id: int) -> int:
    return __img_stats[image_id]['width']


@_fenetre_creee
def modifie_image(image_id: int, hauteur: int, largeur: int, angle: int) -> None:
    """
    Modifie (redimensionne et tourne) l'image désignée par ``objet_ou_tag``.

    :param image_id: identifiant de l'image à modifier
    :param int largeur: nouvelle largeur de l'image
    :param int hauteur: nouvelle hauteur de l'image
    :param int angle: nouvel angle de rotation de l'image
    """
    assert __canevas is not None
    stats = __img_stats[image_id]
    fichier = stats["file"]
    if PIL_AVAILABLE:
        tk_img = _load_pil_image(fichier, hauteur, largeur, angle)
    else:
        tk_img = _load_tk_image(fichier, hauteur, largeur, angle)
        angle = 0
    stats["angle"] = angle
    stats["height"] = tk_img.height()
    stats["width"] = tk_img.width()
    __canevas.canvas.itemconfig(image_id, image=tk_img)


@_fenetre_creee
def rotation_image(objet_ou_tag: Union[int, str],
                   angle: float) -> None:
    """
    Tourne l'image ``image`` d'un angle ``angle``.

    :param objet_ou_tag: identifiant de l'image ou de l'étiquette de l'image à rotationner
    :param int angle: angle de rotation de l'image
    :return: identifiant d'objet
    """
    assert __canevas is not None
    objet = _locate_object(objet_ou_tag)
    stats = __img_stats[objet]
    angle += stats["angle"]
    modifie_image(objet, hauteur_image(objet), largeur_image(objet), angle)


@_fenetre_creee
def redimensionne_image(objet_ou_tag: Union[int, str],
                        facteur: float) -> None:
    """
    Redimensionne l'image ``image`` à la taille ``longueur`` x ``largeur``.

    :param objet_ou_tag: identifiant de l'image ou de l'étiquette de l'image à redimensionner
    :param int facteur: facteur d'agrandissement ou réduction
    :return: identifiant d'objet
    """

    assert __canevas is not None
    objet = _locate_object(objet_ou_tag)
    stats = __img_stats[objet]
    angle = stats["angle"]
    hauteur = int(stats["height"] * facteur)
    largeur = int(stats["width"] * facteur)
    modifie_image(objet, hauteur, largeur, angle)


# Texte


@_fenetre_creee
def texte(
        x: float,
        y: float,
        chaine: str,
        couleur: str = "black",
        remplissage: str = "black",
        ancrage: Anchor = "nw",
        police: str = "Helvetica",
        taille: int = 24,
        tag: str = "",
) -> int:
    """
    Affiche la chaîne ``chaine`` avec ``(x, y)`` comme point d'ancrage (par
    défaut le coin supérieur gauche).

    :param float x: abscisse du point d'ancrage
    :param float y: ordonnée du point d'ancrage
    :param str chaine: texte à afficher
    :param str couleur: couleur de texte (défaut 'black')
    :param str remplissage: synonyme de `couleur` (défaut 'black')
    :param ancrage: position du point d'ancrage (défaut 'nw')
    :param police: police de caractères (défaut : `Helvetica`)
    :param taille: taille de police (défaut 24)
    :param tag: étiquette d'objet (défaut : pas d'étiquette
    :return: identificateur d'objet
    """
    assert __canevas is not None
    if remplissage and not couleur:
        couleur = remplissage
    return __canevas.canvas.create_text(
        x, y,
        text=chaine, font=(police, taille),
        tags=tag, fill=couleur, anchor=ancrage
    )


def taille_texte(
        chaine: str, police: str = "Helvetica", taille: int = 24
) -> Tuple[int, int]:
    """
    Donne la largeur et la hauteur en pixel nécessaires pour afficher
    ``chaine`` dans la police et la taille données.

    :param str chaine: chaîne à mesurer
    :param police: police de caractères (défaut : `Helvetica`)
    :param taille: taille de police (défaut 24)
    :return: couple (w, h) constitué de la largeur et la hauteur de la chaîne
        en pixels (int), dans la police et la taille données.
    """
    font = Font(family=police, size=taille)
    return font.measure(chaine), font.metrics("linespace")


#############################################################################
# Utilitaires sur les objets
#############################################################################


@_fenetre_creee
def efface_tout() -> None:
    """
    Efface la fenêtre.
    """
    assert __canevas is not None
    __canevas.canvas.delete("all")


@_fenetre_creee
def efface(objet_ou_tag: Union[int, str]) -> None:
    """
    Efface ``objet`` de la fenêtre.

    :param: objet ou étiquette d'objet à supprimer
    :type: ``int`` ou ``str``
    """
    assert __canevas is not None
    __canevas.canvas.delete(objet_ou_tag)


@_fenetre_creee
def type_objet(objet: int) -> Optional[str]:
    assert __canevas is not None
    tobj: Optional[str] = __canevas.canvas.type(objet)  # type: ignore
    if tobj is None:
        return None
    if tobj == "oval":
        ax, ay, bx, by = __canevas.canvas.coords(objet)
        return "cercle" if bx - ax == by - ay else None
    return __trans_object_type.get(tobj, None)


@_fenetre_creee
def recuperer_tags(identifiant: int) -> Tuple[str, ...]:
    """
    Renvoie les tags d'un objet

    :param identifiant: identifiant de l'objet

    :return tags: Tuple contenant les tags de l'objet. Peut être vide.
    """
    assert __canevas is not None
    assert isinstance(identifiant, int)
    return __canevas.canvas.gettags(identifiant)


@_fenetre_creee
def modifie(objet_ou_tag: Union[int, str], **options: Dict[str, str]) -> None:
    assert __canevas is not None
    if (type_objet(objet_ou_tag) == "texte"
            and "couleur" in options
            and "remplissage" not in options):
        options["remplissage"] = options["couleur"]
        del options["couleur"]
    temp = {}
    for option, valeur in options.items():
        if option in __trans_options:
            temp[__trans_options[option]] = valeur
    __canevas.canvas.itemconfigure(objet_ou_tag, **temp)


@_fenetre_creee
def deplace(objet_ou_tag: Union[int, str],
            distance_x: Union[int, float],
            distance_y: Union[int, float]) -> None:
    assert __canevas is not None
    __canevas.canvas.move(objet_ou_tag, distance_x, distance_y)


@_fenetre_creee
def couleur(objet: int) -> Optional[str]:
    assert __canevas is not None
    if type_objet(objet) == 'texte':
        option = "fill"
    else:
        option = "outline"
    return __canevas.canvas.itemcget(objet, option=option)  # type: ignore


@_fenetre_creee
def remplissage(objet: int) -> Optional[str]:
    assert __canevas is not None
    return __canevas.canvas.itemcget(objet, option="fill")  # type: ignore


#############################################################################
# Utilitaires
#############################################################################


def attente(temps: float) -> None:
    start = time()
    while time() - start < temps:
        mise_a_jour()


@_fenetre_creee
def capture_ecran(file: str) -> None:
    """
    Fait une capture d'écran sauvegardée dans ``file.png``.
    """
    assert __canevas is not None
    __canevas.canvas.postscript(
        file=file + ".ps",
        height=__canevas.height,
        width=__canevas.width,
        colormode="color",
    )

    subprocess.call(
        "convert -density 150 -geometry 100% -background white -flatten"
        " " + file + ".ps " + file + ".png",
        shell=True,
    )
    subprocess.call("rm " + file + ".ps", shell=True)


@_fenetre_creee
def touche_pressee(keysym: str) -> bool:
    """
    Renvoie `True` si ``keysym`` est actuellement pressée.

    Cette fonction est utile pour la gestion des touches de déplacement dans un jeu
    car elle permet une animation mieux maîtrisée, en évitant le phénomène de répétition
    de touche lié au système d'exploitation.

    :param keysym: symbole associé à la touche à tester.
    :return: `True` si ``keysym`` est actuellement pressée, `False` sinon.
    """
    assert __canevas is not None
    return keysym in __canevas.pressed_keys


@_fenetre_creee
def repere(grad: int = 50,
           sous_grad : Union[int, None] = 10,
           valeurs: bool = True,
           couleur_grad: str = "#a0a0a0",
           couleur_sous_grad: str = "#bbbbbb") -> None:
    """affiche une grille sur la fenêtre.
    :param grad: distance en pixels entre deux graduations majeures
    :param sous_grad: distance en pixels entre deux graduations mineures, ou None
    :param valeurs: True (defaut) pour affichage des valeurs, False sinon
    :param couleur_grad: couleur des graduations majeures et du texte
    :param couleur_sous_grad: couleur des graduations mineures
    """
    assert __canevas is not None
    offset = 2
    __canevas.canvas.create_text(offset, offset, text="0", fill=couleur_grad,
                                 tags='repere', anchor='nw', font=('Helvetica', 8))
    pas = grad if sous_grad is None else sous_grad
    xy = pas
    xmax = __canevas.width
    ymax = __canevas.height
    while xy < max(xmax, ymax) :
        if xy % grad == 0:
            couleur = couleur_grad
            dash : Union[str, int] = ""
            if valeurs:
                __canevas.canvas.create_text(xy + offset, 0, text=xy, fill=couleur,
                                 tags='repere', anchor='nw', font=('Helvetica', 8))
                __canevas.canvas.create_text(0, xy + offset, text=xy, fill=couleur,
                                 tags='repere', anchor='nw', font=('Helvetica', 8))
        else:
            couleur = couleur_sous_grad
            dash = 2
        __canevas.canvas.create_line(xy, 0, xy, ymax, fill=couleur, dash=dash, tags='repere')
        __canevas.canvas.create_line(0, xy, xmax, xy, fill=couleur, dash=dash, tags='repere')
        xy += pas


#############################################################################
# Gestions des évènements
#############################################################################


@_fenetre_creee
def donne_ev() -> Optional[FltkEvent]:
    """
    Renvoie immédiatement l'événement en attente le plus ancien,
    ou ``None`` si aucun événement n'est en attente.
    """
    assert __canevas is not None
    if not __canevas.ev_queue:
        return None
    return __canevas.ev_queue.popleft()


def attend_ev() -> FltkEvent:
    """Attend qu'un événement ait lieu et renvoie le premier événement qui
    se produit."""
    while True:
        ev = donne_ev()
        if ev is not None:
            return ev
        mise_a_jour()


def attend_clic_gauche() -> Tuple[int, int]:
    """Attend qu'un clic gauche sur la fenêtre ait lieu et renvoie ses
    coordonnées. **Attention**, cette fonction empêche la détection d'autres
    événements ou la fermeture de la fenêtre."""
    while True:
        ev = donne_ev()
        if ev is not None and type_ev(ev) == "ClicGauche":
            x, y = abscisse(ev), ordonnee(ev)
            assert isinstance(x, int) and isinstance(y, int)
            return x, y
        mise_a_jour()


def attend_fermeture() -> None:
    """Attend la fermeture de la fenêtre. Cette fonction renvoie None.
    **Attention**, cette fonction empêche la détection d'autres événements."""
    while True:
        ev = donne_ev()
        if ev is not None and type_ev(ev) == "Quitte":
            ferme_fenetre()
            return
        mise_a_jour()


def type_ev(ev: Optional[FltkEvent]) -> Optional[str]:
    """
    Renvoie une chaîne donnant le type de ``ev``. Les types
    possibles sont 'ClicDroit', 'ClicGauche', 'Touche' et 'Quitte'.
    Renvoie ``None`` si ``evenement`` vaut ``None``.
    """
    return ev if ev is None else ev[0]


def abscisse(ev: Optional[FltkEvent]) -> Optional[int]:
    """
    Renvoie la coordonnée x associé à ``ev`` si elle existe, None sinon.
    """
    x = _attribut(ev, "x")
    assert isinstance(x, int) or x is None
    return x


def ordonnee(ev: Optional[FltkEvent]) -> Optional[int]:
    """
    Renvoie la coordonnée y associé à ``ev`` si elle existe, None sinon.
    """
    y = _attribut(ev, "y")
    assert isinstance(y, int) or y is None
    return y


def touche(ev: Optional[FltkEvent]) -> str:
    """
    Renvoie une chaîne correspondant à la touche associé à ``ev``,
    si elle existe.
    """
    keysym = _attribut(ev, "keysym")
    assert isinstance(keysym, str)
    return keysym


def _attribut(ev: Optional[FltkEvent], nom: str) -> Any:
    """
    Renvoie l'attribut `nom` de l'événement `ev`, s'il existe.

    Provoque une erreur ``TypeEvenementNonValide`` si `ev` est `None` ou ne
    possède pas l'attribut `nom`.

    :param ev: événement fltk
    :param nom: nom de l'attribut d'événement à renvoyer
    :return: valeur associée à l'attribut `nom` dans `ev`
    """
    if ev is None:
        raise TypeEvenementNonValide(
            f"Accès à l'attribut {nom} impossible sur un événement vide"
        )
    tev, evtk = ev
    if not hasattr(evtk, nom):
        raise TypeEvenementNonValide(
            f"Accès à l'attribut {nom} impossible "
            f"sur un événement de type {tev}"
        )
    attr = getattr(evtk, nom)
    return attr if attr != "??" else None


#############################################################################
# Informations sur la fenêtre
#############################################################################


@_fenetre_creee
def abscisse_souris() -> int:
    """
    Renvoie l'abscisse actuelle du pointeur de souris par rapport au bord
    gauche de la zone de dessin.
    """
    assert __canevas is not None
    return __canevas.canvas.winfo_pointerx() - __canevas.canvas.winfo_rootx()


@_fenetre_creee
def ordonnee_souris() -> int:
    """
    Renvoie l'ordonnée actuelle du pointeur de souris par rapport au bord haut
    de la zone de dessin.
    """
    assert __canevas is not None
    return __canevas.canvas.winfo_pointery() - __canevas.canvas.winfo_rooty()


@_fenetre_creee
def largeur_fenetre() -> int:
    """
    Renvoie la largeur actuelle de la zone de dessin.
    """
    assert __canevas is not None
    return __canevas.width


@_fenetre_creee
def hauteur_fenetre() -> int:
    """
    Renvoie la hauteur actuelle de la zone de dessin.
    """
    assert __canevas is not None
    return __canevas.height


@_fenetre_creee
def liste_objets_survoles() -> Tuple[int, ...]:
    """
    Renvoie l'identifiant de tous les objets actuellement survolés
    """
    assert __canevas is not None
    x, y = abscisse_souris(), ordonnee_souris()
    overlapping = __canevas.canvas.find_overlapping(x, y, x, y)
    return overlapping

@_fenetre_creee
def objet_survole() -> Optional[int]:
    """
    Renvoie un objet actuellement survolé
    """
    assert __canevas is not None
    overlapping = liste_objets_survoles()
    if overlapping:
        return overlapping[0]
    return None


@_fenetre_creee
def est_objet_survole(objet_ou_tag : Union[int, str, List[str]]) -> bool:
    """
    Renvoie si un objet qui vérifie les conditions d'id ou de tags données est survolé.

    Si objet_ou_tag est un int, check si l'objet avec cet identifiant est survolé.
    Si c'est un str, check si un objet avec ce tag l'est
    Si c'est une liste, check si un objet qui remplit toutes ces contraintes l'est

    :param objet_ou_tag: Contrainte(s) sur les objets
    """
    assert __canevas is not None
    if isinstance(objet_ou_tag, int):
        return objet_ou_tag in liste_objets_survoles()
    if isinstance(objet_ou_tag, str):
        tags = tuple([objet_ou_tag])
        return any(
            tag_obj in tags for obj in liste_objets_survoles() for tag_obj in recuperer_tags(obj)
        )
    if isinstance(objet_ou_tag, list):
        return all(est_objet_survole(tag) for tag in objet_ou_tag)
    raise TypeError("Argument de type incorrect")
