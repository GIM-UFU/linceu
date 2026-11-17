"""
linceu.regiao.campo_equivalente
==================================

Calcula o **campo equivalente**: a projeção do Campo Óptico de
Referência de uma configuração de microscópio
(:class:`~linceu.microscopia.campo_optico.CampoOpticoReferencia`)
sobre o espaço de pixels de uma imagem de scanner calibrada, centrada
em um ponto arbitrário dessa imagem.

Isso responde à pergunta "se eu olhasse esta lâmina ao microscópio,
centrado neste ponto, qual região da imagem digitalizada eu estaria
vendo?" — expressando o campo óptico circular do microscópio tanto em
unidades físicas quanto em pixels da imagem do scanner, através da
calibração do scanner (micra por pixel).

:class:`CampoEquivalente` é o modelo geométrico do campo: possui
centro, diâmetro e área, cada um disponível tanto em pixels quanto em
unidades físicas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from linceu.geometria.circulo import Circulo
from linceu.geometria.unidades import Area, Comprimento, UnidadeArea
from linceu.microscopia.campo_optico import CampoOpticoReferencia
from linceu.scanner.calibracao import ParametrosCalibracao


@dataclass(frozen=True, slots=True)
class CampoEquivalente:
    """Modelo geométrico do campo óptico de um microscópio, projetado
    sobre uma imagem de scanner calibrada e centrado em um ponto dela.

    Atributos
    ----------
    circulo:
        A geometria circular física do campo (diâmetro + área),
        herdada diretamente do
        :class:`~linceu.microscopia.campo_optico.CampoOpticoReferencia`
        de origem.
    calibracao:
        A calibração do scanner (micra por pixel) usada para projetar
        o campo físico em pixels.
    centro_x_px, centro_y_px:
        Coordenadas do centro do campo na imagem do scanner, em
        pixels, no nível de pirâmide ao qual ``calibracao`` se refere
        (``calibracao.nivel``).
    """

    circulo: Circulo
    calibracao: ParametrosCalibracao
    centro_x_px: float
    centro_y_px: float

    @property
    def diametro(self) -> Comprimento:
        """Diâmetro físico do campo (ex.: em milímetros)."""
        return self.circulo.diametro

    @property
    def area(self) -> Area:
        """Área física do campo (ex.: em milímetros quadrados)."""
        return self.circulo.area

    @property
    def diametro_px(self) -> float:
        """Diâmetro do campo expresso em pixels da imagem do scanner,
        ao longo do eixo X (usa ``calibracao.micra_x``)."""
        return self.calibracao.pixels_x(self.diametro)

    @property
    def raio_px(self) -> float:
        """Raio do campo expresso em pixels da imagem do scanner."""
        return self.diametro_px / 2.0

    @property
    def area_px(self) -> Area:
        """Área do campo expressa em pixels quadrados da imagem do
        scanner.

        Calculada diretamente a partir do raio em pixels de cada eixo
        (:math:`A = \\pi \\cdot r_x \\cdot r_y`) em vez de reusar a
        conversão isotrópica de
        :meth:`~linceu.geometria.unidades.Area.converter_para`, já que
        pixels não quadrados (``micra_x != micra_y``) fariam essa
        conversão isotrópica produzir um valor incorreto.
        """
        return Area(math.pi * self.raio_px * self._raio_px_y, UnidadeArea.PIXEL_QUADRADO)

    @property
    def _raio_px_y(self) -> float:
        """Raio do campo em pixels ao longo do eixo Y (usa
        ``calibracao.micra_y``); auxiliar interno de :attr:`area_px`."""
        return self.calibracao.pixels_y(self.diametro) / 2.0

    @property
    def centro_px(self) -> tuple[float, float]:
        """Centro do campo na imagem do scanner, como ``(x, y)`` em
        pixels."""
        return (self.centro_x_px, self.centro_y_px)

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (
            f"CampoEquivalente(centro=({self.centro_x_px:g},{self.centro_y_px:g})px, "
            f"D={self.diametro!r}, D_px={self.diametro_px:.1f}px)"
        )


def calcular_campo_equivalente(
    campo_referencia: CampoOpticoReferencia,
    calibracao: ParametrosCalibracao,
    centro_x_px: float,
    centro_y_px: float,
) -> CampoEquivalente:
    """Calcula o :class:`CampoEquivalente` do campo óptico
    ``campo_referencia`` projetado sobre uma imagem de scanner
    calibrada por ``calibracao``, centrado em ``(centro_x_px, centro_y_px)``.

    Parâmetros
    ----------
    campo_referencia:
        O Campo Óptico de Referência da configuração de microscópio
        (ocular + objetiva) sendo projetado.
    calibracao:
        A calibração (micra por pixel) da imagem do scanner de
        destino, no nível de pirâmide desejado.
    centro_x_px, centro_y_px:
        O ponto, em pixels da imagem do scanner, sobre o qual o campo
        deve ser centrado.

    Retorna
    -------
    CampoEquivalente
    """
    return CampoEquivalente(
        circulo=campo_referencia.circulo,
        calibracao=calibracao,
        centro_x_px=centro_x_px,
        centro_y_px=centro_y_px,
    )
