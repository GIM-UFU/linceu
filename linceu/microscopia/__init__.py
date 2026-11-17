"""
linceu.microscopia
=====================

Modela a configuração óptica de um microscópio convencional
(:class:`~linceu.microscopia.ocular.Ocular`,
:class:`~linceu.microscopia.objetiva.Objetiva`,
:class:`~linceu.microscopia.microscopio.Microscopio`) e deriva dela o
Campo Óptico de Referência
(:class:`~linceu.microscopia.campo_optico.CampoOpticoReferencia`, COR):
o campo de visão físico produzido por uma configuração de microscópio
composta por uma lente objetiva e uma lente ocular específicas.

    D_COR = FN / M
    A_COR = pi * (D_COR / 2)^2

onde ``FN`` é o número de campo da ocular (mm) e ``M`` é a ampliação
da objetiva (adimensional).
"""

from linceu.microscopia.campo_optico import CampoOpticoReferencia
from linceu.microscopia.microscopio import Microscopio
from linceu.microscopia.objetiva import Objetiva
from linceu.microscopia.ocular import Ocular

__all__ = ["CampoOpticoReferencia", "Microscopio", "Objetiva", "Ocular"]
