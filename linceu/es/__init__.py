"""
linceu.es
===========

Entrada/saída de imagens de lâmina inteira. Contém o único adaptador
concreto da biblioteca, :class:`~linceu.es.tiff.LeitorTiff`, que lê
metadados e regiões de pixel de arquivos TIFF e BigTIFF (``.tif``,
``.tiff``, ``.btf``) via ``tifffile``.
"""

from linceu.es.tiff import EXTENSOES_SUPORTADAS, LeitorTiff

__all__ = ["EXTENSOES_SUPORTADAS", "LeitorTiff"]
