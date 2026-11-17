"""
linceu.geometria.area
========================

Auxiliares derivados de área, em particular :class:`RazaoArea`: o
valor adimensional produzido quando uma :class:`~linceu.geometria.unidades.Area`
é dividida por outra — por exemplo, a razão entre a área de uma imagem
e a área do campo equivalente de um microscópio, calculada em
:mod:`linceu.regiao`.

Manter ``RazaoArea`` aqui (em vez de expor razões de área como um
``float`` puro) preserva a rastreabilidade: toda grandeza adimensional
da biblioteca ainda se lembra de quais duas áreas a produziram, o que é
essencial para a proveniência e para as verificações de consistência
dimensional realizadas pelo código cliente.
"""

from __future__ import annotations

from dataclasses import dataclass

from linceu.geometria.unidades import Area
from linceu.utilitarios.excecoes import ErroIncompatibilidadeUnidade
from linceu.utilitarios.validacao import exigir_positivo


@dataclass(frozen=True, slots=True)
class RazaoArea:
    """Uma razão adimensional imutável entre duas áreas.

    .. math::
        r = \\frac{A_{numerador}}{A_{denominador}}

    Atributos
    ----------
    valor:
        A própria razão adimensional.
    numerador:
        A área usada como numerador (mantida para proveniência/auditoria).
    denominador:
        A área usada como denominador (mantida para proveniência/auditoria).
    """

    valor: float
    numerador: Area
    denominador: Area

    @classmethod
    def de(cls, numerador: Area, denominador: Area) -> RazaoArea:
        """Calcula ``numerador / denominador`` como uma :class:`RazaoArea`.

        Ambas as áreas devem compartilhar a mesma
        :class:`~linceu.geometria.unidades.UnidadeArea`; é
        responsabilidade do chamador invocar ``.converter_para(...)``
        antecipadamente caso uma conversão seja necessária. Isso
        espelha :meth:`Area.__truediv__` e existe como uma alternativa
        nomeada e autodocumentada ao operador ``/`` puro, para uso na
        camada de normalização.

        Levanta
        -------
        ErroIncompatibilidadeUnidade
            Se as duas áreas não compartilharem uma unidade, ou se o
            denominador for zero.
        """
        if numerador.unidade != denominador.unidade:
            raise ErroIncompatibilidadeUnidade(
                f"RazaoArea exige unidades correspondentes; recebido "
                f"{numerador.unidade.simbolo} e {denominador.unidade.simbolo}."
            )
        exigir_positivo(
            denominador.valor, "RazaoArea.denominador.valor", excecao=ErroIncompatibilidadeUnidade
        )
        return cls(valor=numerador.valor / denominador.valor, numerador=numerador, denominador=denominador)

    def __float__(self) -> float:
        return self.valor

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"RazaoArea({self.valor:.6f})"
