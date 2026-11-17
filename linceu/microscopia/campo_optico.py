"""
linceu.microscopia.campo_optico
==================================

Implementa a **Definição 1 — Campo Óptico de Referência (COR)**.

    Um Campo Óptico de Referência (COR) é o campo de visão físico
    produzido por uma configuração de microscópio composta por uma
    lente objetiva e uma lente ocular específicas.

    D_COR = FN / M
    A_COR = pi * (D_COR / 2)^2

onde ``FN`` é o número de campo da ocular (mm) e ``M`` é a ampliação
da objetiva (adimensional). Toda configuração de microscópio define,
portanto, um COR único e imutável.
"""

from __future__ import annotations

from dataclasses import dataclass

from linceu.geometria.circulo import Circulo
from linceu.geometria.unidades import Area, Comprimento, UnidadeComprimento
from linceu.microscopia.objetiva import Objetiva
from linceu.microscopia.ocular import Ocular


@dataclass(frozen=True, slots=True)
class CampoOpticoReferencia:
    """Um Campo Óptico de Referência (COR) imutável.

    Um ``CampoOpticoReferencia`` é totalmente determinado por um par
    :class:`~linceu.microscopia.ocular.Ocular` e
    :class:`~linceu.microscopia.objetiva.Objetiva` via
    :meth:`a_partir_de_configuracao_microscopio`; a construção direta
    a partir de um diâmetro pré-calculado também é suportada para
    casos em que FN/M não são individualmente conhecidos (ex.: um COR
    especificado pelo fabricante).

    Atributos
    ----------
    circulo:
        A geometria circular subjacente (diâmetro + área derivada).
    rotulo:
        Identificador opcional legível por humanos (ex.: ``"100x/FN22
        (imersão em óleo)"``), usado apenas para fins de proveniência
        e relatórios.
    """

    circulo: Circulo
    rotulo: str | None = None

    @classmethod
    def a_partir_de_configuracao_microscopio(
        cls,
        ocular: Ocular,
        objetiva: Objetiva,
        rotulo: str | None = None,
    ) -> CampoOpticoReferencia:
        """Constrói o COR induzido por um dado par ocular/objetiva.

        .. math::
            D_{COR} = \\frac{FN}{M}, \\qquad
            A_{COR} = \\pi \\left(\\frac{D_{COR}}{2}\\right)^2

        Parâmetros
        ----------
        ocular:
            Fornece o número de campo ``FN`` (mm).
        objetiva:
            Fornece a ampliação ``M``.
        rotulo:
            Rótulo descritivo opcional para o campo resultante.

        Retorna
        -------
        CampoOpticoReferencia
        """
        diametro_mm = ocular.numero_campo / objetiva.ampliacao
        diametro = Comprimento(diametro_mm, UnidadeComprimento.MILIMETRO)
        return cls(circulo=Circulo(diametro=diametro), rotulo=rotulo)

    @classmethod
    def a_partir_de_diametro(cls, diametro: Comprimento, rotulo: str | None = None) -> CampoOpticoReferencia:
        """Constrói um COR diretamente a partir de um diâmetro de
        campo conhecido, contornando a decomposição FN/M. Útil quando
        apenas o diâmetro do campo de visão publicado pelo fabricante
        está disponível."""
        return cls(circulo=Circulo(diametro=diametro), rotulo=rotulo)

    @property
    def diametro(self) -> Comprimento:
        """Diâmetro físico do campo óptico."""
        return self.circulo.diametro

    @property
    def area(self) -> Area:
        """Área física do campo de referência — satisfaz o protocolo
        estrutural :class:`~linceu.geometria.campo.TemArea`, o que é o
        que permite que este objeto seja consumido diretamente pelos
        cálculos de campo equivalente em :mod:`linceu.regiao`."""
        return self.circulo.area

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        tag = f" [{self.rotulo}]" if self.rotulo else ""
        return f"CampoOpticoReferencia(D={self.diametro!r}, A={self.area!r}){tag}"
