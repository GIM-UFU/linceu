"""
linceu.geometria
===================

Primitivas geométricas dimensionalmente seguras, usadas em toda a
biblioteca: :class:`~linceu.geometria.unidades.Comprimento` e
:class:`~linceu.geometria.unidades.Area` rotulados com unidade,
matemática de campo circular (:mod:`linceu.geometria.circulo`), razões
de área adimensionais (:class:`~linceu.geometria.area.RazaoArea`), e o
protocolo estrutural :class:`~linceu.geometria.campo.TemArea`.

Este subpacote não tem dependência de conceitos de microscopia,
scanner ou E/S, e é intencionalmente reutilizável em qualquer contexto
de imageamento quantitativo.
"""

from linceu.geometria.area import RazaoArea
from linceu.geometria.campo import TemArea
from linceu.geometria.circulo import Circulo, area_para_diametro, diametro_para_area, raio_para_area
from linceu.geometria.unidades import Area, Comprimento, UnidadeArea, UnidadeComprimento, unidade_area_para

__all__ = [
    "Area",
    "Circulo",
    "Comprimento",
    "RazaoArea",
    "TemArea",
    "UnidadeArea",
    "UnidadeComprimento",
    "area_para_diametro",
    "diametro_para_area",
    "raio_para_area",
    "unidade_area_para",
]
