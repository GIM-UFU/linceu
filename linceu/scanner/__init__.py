"""
linceu.scanner
=================

Representa a configuração de aquisição de lâminas digitais: metadados
de lâmina inteira e pirâmide de resoluções
(:mod:`linceu.scanner.metadados`), calibração de fatores de conversão
pixel-para-físico (:mod:`linceu.scanner.calibracao`), representação de
regiões de imagem calibradas e posicionadas
(:mod:`linceu.scanner.imagem`), e conversão de coordenadas entre
níveis de pirâmide (:mod:`linceu.scanner.piramide`).

Este subpacote é deliberadamente independente de
:mod:`linceu.microscopia`: ele foca exclusivamente na representação da
aquisição de imagens digitais, não em definições de campo óptico. A
leitura de arquivo em si (TIFF/BigTIFF) fica em :mod:`linceu.es`.
"""

from linceu.scanner.calibracao import ParametrosCalibracao, calibrar
from linceu.scanner.imagem import ImagemDigital
from linceu.scanner.metadados import MetadadosScanner, NivelPiramide
from linceu.scanner.piramide import converter_caixa_pixels, converter_coordenada, converter_dimensao

__all__ = [
    "ImagemDigital",
    "MetadadosScanner",
    "NivelPiramide",
    "ParametrosCalibracao",
    "calibrar",
    "converter_caixa_pixels",
    "converter_coordenada",
    "converter_dimensao",
]
