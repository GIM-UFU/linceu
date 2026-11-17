"""
linceu.microscopia.microscopio
=================================

``Microscopio`` é um pequeno agregado que combina uma
:class:`~linceu.microscopia.ocular.Ocular` com uma
:class:`~linceu.microscopia.objetiva.Objetiva` e expõe o
:class:`~linceu.microscopia.campo_optico.CampoOpticoReferencia`
resultante como uma propriedade derivada, sem memoização (é barato
recalcular, e recalcular evita um invariante de estado redundante
entre o agregado e suas partes).

Todo par distinto ``(Ocular, Objetiva)`` é, pela Definição 1, uma
*configuração* de microscópio distinta — logo, um COR distinto. Esta
classe é o "objeto computacional de primeira classe" mencionado na
descrição do Módulo de Microscopia da especificação.
"""

from __future__ import annotations

from dataclasses import dataclass

from linceu.microscopia.campo_optico import CampoOpticoReferencia
from linceu.microscopia.objetiva import Objetiva
from linceu.microscopia.ocular import Ocular


@dataclass(frozen=True, slots=True)
class Microscopio:
    """Uma configuração de microscópio imutável (ocular + objetiva).

    Parâmetros
    ----------
    ocular:
        A ocular em uso.
    objetiva:
        A lente objetiva em uso.
    nome:
        Identificador opcional legível por humanos (ex.: ``"Olympus
        CX23 do Laboratório"``).

    Exemplos
    --------
    >>> escopo = Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0))
    >>> escopo.campo_optico_referencia.diametro
    Comprimento(0.22 mm)
    """

    ocular: Ocular
    objetiva: Objetiva
    nome: str | None = None

    @property
    def ampliacao_total(self) -> float:
        """Ampliação total nominal: ocular x objetiva."""
        return self.ocular.ampliacao * self.objetiva.ampliacao

    @property
    def campo_optico_referencia(self) -> CampoOpticoReferencia:
        """O :class:`CampoOpticoReferencia` único induzido pelo par
        ocular/objetiva deste microscópio (Definição 1)."""
        tag = (
            f"{self.nome} ({self.objetiva.ampliacao:g}x/FN{self.ocular.numero_campo:g})"
            if self.nome
            else None
        )
        return CampoOpticoReferencia.a_partir_de_configuracao_microscopio(
            self.ocular, self.objetiva, rotulo=tag
        )

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        tag = f"{self.nome}: " if self.nome else ""
        return f"Microscopio({tag}{self.objetiva.ampliacao:g}x, FN{self.ocular.numero_campo:g})"
