"""
linceu.microscopia.ocular
============================

Modela a ocular (lente ocular) de um microscópio composto,
especificamente seu **número de campo** (FN) — o diâmetro, em
milímetros, do diafragma de campo visto através da ocular. O FN é
gravado em praticamente toda ocular de microscópio (ex.: "FN 22" para
uma ocular de campo amplo) e é a entrada, do lado da ocular, para o
cálculo do Campo Óptico de Referência (Definição 1 da especificação
que acompanha este framework).
"""

from __future__ import annotations

from dataclasses import dataclass

from linceu.geometria.unidades import Comprimento, UnidadeComprimento
from linceu.utilitarios.validacao import exigir_positivo


@dataclass(frozen=True, slots=True)
class Ocular:
    """Uma representação imutável de uma ocular de microscópio.

    Parâmetros
    ----------
    numero_campo:
        O número de campo (FN), em milímetros — o diâmetro físico da
        abertura do diafragma que define o campo de visão da ocular.
        Deve ser estritamente positivo.
    ampliacao:
        A ampliação própria da ocular (ex.: ``10.0`` para uma ocular
        de 10x). Incluída por completude/relatório; não entra
        diretamente na fórmula do diâmetro do COR (o FN já leva em
        conta o campo angular da ocular), mas é mantida para
        proveniência e para o relatório de ampliação total do sistema.
    modelo:
        Identificador opcional em texto livre do fabricante/modelo.

    Invariantes
    ------------
    * ``numero_campo > 0``
    * ``ampliacao > 0`` quando fornecida.
    """

    numero_campo: float
    ampliacao: float = 10.0
    modelo: str | None = None

    def __post_init__(self) -> None:
        exigir_positivo(self.numero_campo, "Ocular.numero_campo")
        exigir_positivo(self.ampliacao, "Ocular.ampliacao")

    @property
    def comprimento_numero_campo(self) -> Comprimento:
        """O número de campo expresso como um
        :class:`~linceu.geometria.unidades.Comprimento` rotulado com
        unidade, em milímetros."""
        return Comprimento(self.numero_campo, UnidadeComprimento.MILIMETRO)

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"Ocular(FN={self.numero_campo:g}mm, {self.ampliacao:g}x)"
