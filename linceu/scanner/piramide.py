"""
linceu.scanner.piramide
==========================

Conversão de coordenadas de pixel entre níveis de uma pirâmide de
resolução de uma imagem WSI. Uma mesma posição física na lâmina
corresponde a coordenadas de pixel diferentes em cada nível, escaladas
pelo :attr:`~linceu.scanner.metadados.NivelPiramide.fator_downsample`
relativo de cada nível.
"""

from __future__ import annotations

from linceu.scanner.metadados import NivelPiramide


def converter_coordenada(
    x: float, y: float, origem: NivelPiramide, destino: NivelPiramide
) -> tuple[float, float]:
    """Converte uma coordenada de pixel ``(x, y)`` expressa no nível
    ``origem`` para a coordenada equivalente no nível ``destino``.

    .. math::
        x_{destino} = x_{origem} \\cdot \\frac{f_{origem}}{f_{destino}}

    onde :math:`f` é o fator de downsample de cada nível relativo ao
    nível 0. Ambos os níveis devem pertencer à mesma pirâmide (mesma
    imagem de origem); esta função não valida isso, apenas aplica a
    razão de escala.
    """
    fator = origem.fator_downsample / destino.fator_downsample
    return (x * fator, y * fator)


def converter_dimensao(
    largura: float, altura: float, origem: NivelPiramide, destino: NivelPiramide
) -> tuple[float, float]:
    """Converte uma dimensão ``(largura, altura)`` expressa em pixels
    do nível ``origem`` para a dimensão equivalente no nível ``destino``,
    pela mesma razão de escala usada em :func:`converter_coordenada`.
    """
    return converter_coordenada(largura, altura, origem, destino)


def converter_caixa_pixels(
    caixa: tuple[float, float, float, float], origem: NivelPiramide, destino: NivelPiramide
) -> tuple[float, float, float, float]:
    """Converte uma caixa delimitadora ``(x0, y0, x1, y1)`` do nível
    ``origem`` para o nível ``destino``."""
    x0, y0, x1, y1 = caixa
    nx0, ny0 = converter_coordenada(x0, y0, origem, destino)
    nx1, ny1 = converter_coordenada(x1, y1, origem, destino)
    return (nx0, ny0, nx1, ny1)
