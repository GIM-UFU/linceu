"""
linceu.geometria.unidades
============================

Sistema de unidades dimensionalmente seguro para o framework ``linceu``.

Toda grandeza física que percorre o framework (diâmetros de campo,
dimensões de imagem, tamanhos de pixel, áreas de campo óptico) é
representada por um objeto de valor explícito e imutável que carrega
sua unidade junto ao valor numérico. Operações aritméticas entre
unidades incompatíveis (ex.: um comprimento em milímetros somado a uma
área em micrômetros quadrados) levantam
:class:`~linceu.utilitarios.excecoes.ErroIncompatibilidadeUnidade` em
vez de silenciosamente produzir um número errado — esta é a única
decisão de design que evita toda uma classe de bugs metrológicos.

Duas famílias de unidades são definidas:

* :class:`UnidadeComprimento` — unidades unidimensionais (µm, mm, cm, pixel).
* :class:`UnidadeArea` — unidades bidimensionais, derivadas
  multiplicativamente das unidades de comprimento (µm², mm², cm², pixel²).

``pixel`` é tratado como uma unidade de primeira classe porque imagens
digitais brutas são nativamente expressas em pixels; converter um
comprimento em pixels para um comprimento físico exige um fator de
calibração explícito (micra por pixel), motivo pelo qual
:attr:`UnidadeComprimento.PIXEL` não possui fator de conversão fixo
para as unidades métricas — veja :meth:`Comprimento.converter_para`
para mais detalhes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from linceu.utilitarios.excecoes import ErroIncompatibilidadeUnidade
from linceu.utilitarios.validacao import exigir_nao_negativo, exigir_positivo


class UnidadeComprimento(Enum):
    """Unidades unidimensionais de comprimento físico ou digital.

    O valor do enum é o fator multiplicativo que converte uma unidade
    daquele membro em metros (unidade base do SI), exceto para
    :attr:`PIXEL`, que depende da resolução e portanto não tem fator
    fixo (``None``).
    """

    MICROMETRO = 1e-6
    MILIMETRO = 1e-3
    CENTIMETRO = 1e-2
    METRO = 1.0
    PIXEL = None  # requer uma calibração explícita de micra-por-pixel

    @property
    def simbolo(self) -> str:
        """Símbolo textual da unidade (ex.: ``"mm"``, ``"px"``)."""
        return {
            UnidadeComprimento.MICROMETRO: "\u00b5m",
            UnidadeComprimento.MILIMETRO: "mm",
            UnidadeComprimento.CENTIMETRO: "cm",
            UnidadeComprimento.METRO: "m",
            UnidadeComprimento.PIXEL: "px",
        }[self]

    @property
    def eh_metrico(self) -> bool:
        """Se esta unidade possui um fator de conversão SI fixo."""
        return self.value is not None


class UnidadeArea(Enum):
    """Unidades bidimensionais de área física ou digital.

    Os valores são o fator multiplicativo para metros quadrados,
    espelhando :class:`UnidadeComprimento` e seguindo a mesma
    convenção de que :attr:`PIXEL_QUADRADO` depende da resolução.
    """

    MICROMETRO_QUADRADO = 1e-12
    MILIMETRO_QUADRADO = 1e-6
    CENTIMETRO_QUADRADO = 1e-4
    METRO_QUADRADO = 1.0
    PIXEL_QUADRADO = None

    @property
    def simbolo(self) -> str:
        """Símbolo textual da unidade (ex.: ``"mm"``, ``"px"``)."""
        return {
            UnidadeArea.MICROMETRO_QUADRADO: "\u00b5m\u00b2",
            UnidadeArea.MILIMETRO_QUADRADO: "mm\u00b2",
            UnidadeArea.CENTIMETRO_QUADRADO: "cm\u00b2",
            UnidadeArea.METRO_QUADRADO: "m\u00b2",
            UnidadeArea.PIXEL_QUADRADO: "px\u00b2",
        }[self]

    @property
    def eh_metrico(self) -> bool:
        """Se esta unidade possui um fator de conversão SI fixo."""
        return self.value is not None


# Mapeamento de uma UnidadeComprimento para a UnidadeArea obtida ao
# elevá-la ao quadrado. Usado por operações geométricas (ex.:
# Circulo.area) para manter a unidade da área resultante consistente
# com a unidade do comprimento de entrada, sem que o chamador precise
# especificá-la redundantemente.
_COMPRIMENTO_PARA_AREA: dict[UnidadeComprimento, UnidadeArea] = {
    UnidadeComprimento.MICROMETRO: UnidadeArea.MICROMETRO_QUADRADO,
    UnidadeComprimento.MILIMETRO: UnidadeArea.MILIMETRO_QUADRADO,
    UnidadeComprimento.CENTIMETRO: UnidadeArea.CENTIMETRO_QUADRADO,
    UnidadeComprimento.METRO: UnidadeArea.METRO_QUADRADO,
    UnidadeComprimento.PIXEL: UnidadeArea.PIXEL_QUADRADO,
}


def unidade_area_para(unidade_comprimento: UnidadeComprimento) -> UnidadeArea:
    """Retorna a :class:`UnidadeArea` naturalmente induzida ao elevar
    ``unidade_comprimento`` ao quadrado (ex.: milímetro -> milímetro
    quadrado)."""
    return _COMPRIMENTO_PARA_AREA[unidade_comprimento]


@dataclass(frozen=True, slots=True)
class Comprimento:
    """Um comprimento unidimensional imutável, rotulado com sua unidade.

    Parâmetros
    ----------
    valor:
        Magnitude numérica não negativa.
    unidade:
        A :class:`UnidadeComprimento` em que ``valor`` é expresso.

    Invariantes
    ------------
    * ``valor >= 0`` (comprimentos neste framework são sempre
      magnitudes; direcionalidade não é modelada).

    Exemplos
    --------
    >>> d = Comprimento(18.0, UnidadeComprimento.MILIMETRO)
    >>> d.converter_para(UnidadeComprimento.MICROMETRO)
    Comprimento(18000 µm)
    """

    valor: float
    unidade: UnidadeComprimento

    def __post_init__(self) -> None:
        exigir_nao_negativo(self.valor, "Comprimento.valor")

    def converter_para(
        self, destino: UnidadeComprimento, micra_por_pixel: float | None = None
    ) -> Comprimento:
        """Converte este comprimento para ``destino``.

        Parâmetros
        ----------
        destino:
            Unidade de destino.
        micra_por_pixel:
            Exigido *apenas* ao converter de/para :attr:`UnidadeComprimento.PIXEL`,
            já que pixels não têm tamanho físico fixo — é uma
            propriedade do scanner/objetiva de aquisição, não da
            unidade em si. Deve ser estritamente positivo: um fator de
            calibração igual a zero é fisicamente degenerado e, se
            aceito, produziria uma conversão silenciosamente incorreta
            em vez de sinalizar o problema.

        Levanta
        -------
        ErroIncompatibilidadeUnidade
            Se uma conversão de pixel for solicitada sem
            ``micra_por_pixel``, ou com um ``micra_por_pixel`` não
            estritamente positivo.
        """
        if self.unidade == destino:
            return self

        if self.unidade is UnidadeComprimento.PIXEL or destino is UnidadeComprimento.PIXEL:
            if micra_por_pixel is None:
                raise ErroIncompatibilidadeUnidade(
                    "Converter de/para UnidadeComprimento.PIXEL exige um "
                    "fator de calibração `micra_por_pixel` explícito."
                )
            exigir_positivo(micra_por_pixel, "micra_por_pixel", excecao=ErroIncompatibilidadeUnidade)
            metros = (
                self.valor * micra_por_pixel * UnidadeComprimento.MICROMETRO.value
                if self.unidade is UnidadeComprimento.PIXEL
                else self.valor * self.unidade.value
            )
            if destino is UnidadeComprimento.PIXEL:
                micrometros = metros / UnidadeComprimento.MICROMETRO.value
                return Comprimento(micrometros / micra_por_pixel, UnidadeComprimento.PIXEL)
            return Comprimento(metros / destino.value, destino)

        metros = self.valor * self.unidade.value
        return Comprimento(metros / destino.value, destino)

    def __add__(self, outro: Comprimento) -> Comprimento:
        if not isinstance(outro, Comprimento):
            return NotImplemented
        if self.unidade != outro.unidade:
            raise ErroIncompatibilidadeUnidade(
                f"Não é possível somar Comprimento em {self.unidade.simbolo} a Comprimento em "
                f"{outro.unidade.simbolo} sem uma conversão explícita."
            )
        return Comprimento(self.valor + outro.valor, self.unidade)

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"Comprimento({self.valor:g} {self.unidade.simbolo})"


@dataclass(frozen=True, slots=True)
class Area:
    """Uma área bidimensional imutável, rotulada com sua unidade.

    Veja :class:`Comprimento` para a justificativa geral de design.
    Áreas são produzidas por construtores geométricos (ex.:
    :func:`linceu.geometria.circulo.diametro_para_area`) em vez de
    instanciadas diretamente pela maior parte do código cliente.
    """

    valor: float
    unidade: UnidadeArea

    def __post_init__(self) -> None:
        exigir_nao_negativo(self.valor, "Area.valor")

    def converter_para(self, destino: UnidadeArea, micra_por_pixel: float | None = None) -> Area:
        """Converte esta área para ``destino``, de forma análoga a
        :meth:`Comprimento.converter_para`.

        Para conversões de área em pixels, ``micra_por_pixel`` é
        elevado ao quadrado internamente, já que a área escala com o
        quadrado da resolução linear. Deve ser estritamente positivo
        pelo mesmo motivo descrito em :meth:`Comprimento.converter_para`.
        """
        if self.unidade == destino:
            return self

        if self.unidade is UnidadeArea.PIXEL_QUADRADO or destino is UnidadeArea.PIXEL_QUADRADO:
            if micra_por_pixel is None:
                raise ErroIncompatibilidadeUnidade(
                    "Converter de/para UnidadeArea.PIXEL_QUADRADO exige um "
                    "fator de calibração `micra_por_pixel` explícito."
                )
            exigir_positivo(micra_por_pixel, "micra_por_pixel", excecao=ErroIncompatibilidadeUnidade)
            metros_quadrados_por_px = (micra_por_pixel * UnidadeComprimento.MICROMETRO.value) ** 2
            metros_quadrados = (
                self.valor * metros_quadrados_por_px
                if self.unidade is UnidadeArea.PIXEL_QUADRADO
                else self.valor * self.unidade.value
            )
            if destino is UnidadeArea.PIXEL_QUADRADO:
                return Area(metros_quadrados / metros_quadrados_por_px, destino)
            return Area(metros_quadrados / destino.value, destino)

        metros_quadrados = self.valor * self.unidade.value
        return Area(metros_quadrados / destino.value, destino)

    def __add__(self, outra: Area) -> Area:
        if not isinstance(outra, Area):
            return NotImplemented
        if self.unidade != outra.unidade:
            raise ErroIncompatibilidadeUnidade(
                f"Não é possível somar Area em {self.unidade.simbolo} a Area em "
                f"{outra.unidade.simbolo} sem uma conversão explícita."
            )
        return Area(self.valor + outra.valor, self.unidade)

    def __truediv__(self, outra: Area) -> float:
        """Dividir duas áreas da *mesma unidade* produz uma razão
        adimensional (ex.: a razão entre a área de uma imagem e a área
        de um campo de referência).
        """
        if not isinstance(outra, Area):
            return NotImplemented
        if self.unidade != outra.unidade:
            raise ErroIncompatibilidadeUnidade(
                f"Não é possível dividir Area em {self.unidade.simbolo} por Area em "
                f"{outra.unidade.simbolo} sem uma conversão explícita; "
                f"chame `.converter_para(...)` em um dos operandos primeiro."
            )
        if outra.valor == 0:
            raise ErroIncompatibilidadeUnidade("Divisão por Area de valor zero.")
        return self.valor / outra.valor

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"Area({self.valor:g} {self.unidade.simbolo})"
