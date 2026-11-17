"""
linceu.geometria.circulo
===========================

Primitivas puras de geometria circular.

Os campos de visão do microscópio e o Campo Óptico de Referência
(COR) são modelados como círculos, refletindo a realidade física de
um diafragma de campo circular visualizado através de uma abertura
objetiva também circular. Este módulo contém apenas matemática pura e
sem efeitos colaterais: nenhum vocabulário específico de microscopia
ou de scanner aparece aqui, tornando-o reutilizável em qualquer
contexto de imageamento quantitativo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from linceu.geometria.unidades import Area, Comprimento, UnidadeArea, UnidadeComprimento, unidade_area_para
from linceu.utilitarios.validacao import exigir_nao_negativo


def diametro_para_area(diametro: Comprimento) -> Area:
    """Calcula a área de um círculo a partir do seu diâmetro.

    .. math::
        A = \\pi \\left(\\frac{D}{2}\\right)^2

    Parâmetros
    ----------
    diametro:
        O diâmetro do círculo como um :class:`~linceu.geometria.unidades.Comprimento`
        rotulado com unidade.

    Retorna
    -------
    Area
        A área do círculo, expressa na unidade de área naturalmente
        induzida ao elevar ``diametro.unidade`` ao quadrado (ex.:
        milímetro -> milímetro quadrado).
    """
    raio = diametro.valor / 2.0
    valor_area = math.pi * raio**2
    return Area(valor_area, unidade_area_para(diametro.unidade))


def raio_para_area(raio: Comprimento) -> Area:
    """Calcula a área de um círculo a partir do seu raio.

    .. math::
        A = \\pi r^2
    """
    valor_area = math.pi * raio.valor**2
    return Area(valor_area, unidade_area_para(raio.unidade))


# Inverso de `unidade_area_para`, derivado dela em vez de duplicado à
# mão, para que as duas direções do mapeamento nunca possam divergir.
# Construído uma única vez no import do módulo em vez de recriado a
# cada chamada de `area_para_diametro`.
_AREA_PARA_COMPRIMENTO: dict[UnidadeArea, UnidadeComprimento] = {
    unidade_area_para(unidade): unidade for unidade in UnidadeComprimento
}


def area_para_diametro(area: Area) -> Comprimento:
    """Inverte :func:`diametro_para_area`: recupera o diâmetro que
    produziria a ``area`` circular dada.

    .. math::
        D = 2\\sqrt{\\frac{A}{\\pi}}
    """
    raio = math.sqrt(area.valor / math.pi)
    return Comprimento(2.0 * raio, _AREA_PARA_COMPRIMENTO[area.unidade])


@dataclass(frozen=True, slots=True)
class Circulo:
    """Uma entidade geométrica circular imutável, definida pelo seu diâmetro.

    ``Circulo`` é a representação compartilhada usada tanto pelo campo
    óptico do microscópio (:mod:`linceu.microscopia.campo_optico`)
    quanto, potencialmente, por qualquer outra região circular de
    interesse. Ele expõe ``area`` como uma propriedade derivada,
    calculada na construção, em vez de um campo armazenado, já que é
    totalmente determinada por ``diametro`` (evitando um invariante de
    estado redundante).
    """

    diametro: Comprimento

    def __post_init__(self) -> None:
        exigir_nao_negativo(self.diametro.valor, "Circulo.diametro")

    @property
    def raio(self) -> Comprimento:
        """Raio do círculo, na mesma unidade do diâmetro."""
        return Comprimento(self.diametro.valor / 2.0, self.diametro.unidade)

    @property
    def area(self) -> Area:
        """Área do círculo, na unidade de área correspondente à do diâmetro."""
        return diametro_para_area(self.diametro)

    @classmethod
    def a_partir_de_area(cls, area: Area) -> Circulo:
        """Constrói um :class:`Circulo` a partir de uma área conhecida."""
        return cls(diametro=area_para_diametro(area))

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"Circulo(diametro={self.diametro!r}, area={self.area!r})"
