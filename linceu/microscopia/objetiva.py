"""
linceu.microscopia.objetiva
==============================

Modela a lente objetiva de um microscópio composto: sua ampliação
nominal (M) — a entrada, do lado da objetiva, para o cálculo do Campo
Óptico de Referência.
"""

from __future__ import annotations

from dataclasses import dataclass

from linceu.utilitarios.excecoes import ErroGeometriaInvalida
from linceu.utilitarios.validacao import exigir_positivo


@dataclass(frozen=True, slots=True)
class Objetiva:
    """Uma representação imutável de uma lente objetiva de microscópio.

    Parâmetros
    ----------
    ampliacao:
        A ampliação nominal da objetiva (ex.: ``100.0`` para uma
        objetiva de imersão em óleo de 100x). Deve ser estritamente
        positiva.
    abertura_numerica:
        Abertura numérica (AN) opcional, mantida para proveniência e
        para futuros cálculos relacionados à resolução; não entra na
        fórmula do diâmetro do COR.
    modelo:
        Identificador opcional em texto livre do fabricante/modelo.

    Invariantes
    ------------
    * ``ampliacao > 0``
    * ``0 < abertura_numerica <= 1.6`` quando fornecida (a faixa
      fisicamente alcançável para objetivas de imersão).
    """

    ampliacao: float
    abertura_numerica: float | None = None
    modelo: str | None = None

    def __post_init__(self) -> None:
        exigir_positivo(self.ampliacao, "Objetiva.ampliacao")
        if self.abertura_numerica is not None:
            exigir_positivo(self.abertura_numerica, "Objetiva.abertura_numerica")
            if self.abertura_numerica > 1.6:
                raise ErroGeometriaInvalida(
                    f"Objetiva.abertura_numerica={self.abertura_numerica!r} "
                    f"excede o máximo fisicamente alcançável (~1.6)."
                )

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"Objetiva({self.ampliacao:g}x)"
