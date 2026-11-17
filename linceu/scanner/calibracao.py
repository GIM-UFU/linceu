"""
linceu.scanner.calibracao
============================

Transforma :class:`~linceu.scanner.metadados.MetadadosScanner` brutos
(dimensões em pixels + micra por pixel) em grandezas
:class:`~linceu.geometria.unidades.Comprimento` / :class:`~linceu.geometria.unidades.Area`
fisicamente calibradas. Esta é a única fronteira explícita da
biblioteca onde "pixels" se tornam "distância física".
"""

from __future__ import annotations

from dataclasses import dataclass

from linceu.geometria.unidades import Area, Comprimento, UnidadeArea, UnidadeComprimento
from linceu.scanner.metadados import MetadadosScanner, NivelPiramide
from linceu.utilitarios.excecoes import ErroCalibracao
from linceu.utilitarios.validacao import exigir_inteiro_nao_negativo, exigir_positivo


@dataclass(frozen=True, slots=True)
class ParametrosCalibracao:
    """Fatores de calibração explícitos e auditáveis, extraídos de
    :class:`MetadadosScanner`.

    Separar isto de ``MetadadosScanner`` mantém "o que o scanner
    reportou" (metadados brutos, potencialmente não confiáveis /
    específicos do fabricante) distinto de "qual calibração estamos de
    fato aplicando" (uma decisão deliberada e auditável — ex.: um
    laboratório pode substituir o mpp autorreportado de um scanner por
    um valor obtido de uma lâmina de calibração independente).

    Atributos
    ----------
    micra_x, micra_y:
        Micrômetros por pixel ao longo de X e Y, **no nível indicado por**
        :attr:`nivel`.
    nivel:
        Índice do nível de pirâmide ao qual esta calibração se refere
        (``0`` = resolução plena). Carregar o nível junto da calibração
        impede que coordenadas de um nível sejam lidas, por engano, em
        outro: :class:`~linceu.scanner.imagem.ImagemDigital` e
        :func:`~linceu.regiao.roi.calcular_roi` verificam essa consistência.
    """

    micra_x: float
    micra_y: float
    nivel: int = 0

    def __post_init__(self) -> None:
        exigir_positivo(self.micra_x, "ParametrosCalibracao.micra_x", excecao=ErroCalibracao)
        exigir_positivo(self.micra_y, "ParametrosCalibracao.micra_y", excecao=ErroCalibracao)
        exigir_inteiro_nao_negativo(self.nivel, "ParametrosCalibracao.nivel", excecao=ErroCalibracao)

    @classmethod
    def a_partir_de_metadados(cls, metadados: MetadadosScanner) -> ParametrosCalibracao:
        """Adota os valores de micra-por-pixel autorreportados pelo
        scanner (no nível 0 da pirâmide), literalmente, como a
        calibração a aplicar."""
        return cls(micra_x=metadados.micra_x, micra_y=metadados.micra_y)

    def em_nivel(self, nivel: NivelPiramide) -> ParametrosCalibracao:
        """Deriva a calibração equivalente em um nível de pirâmide mais
        grosseiro, escalando micra-por-pixel pelo ``fator_downsample``
        de ``nivel`` (ex.: em um nível com downsample 4x, cada pixel
        cobre 4x mais distância física em cada eixo). A calibração
        resultante registra ``nivel.indice`` em :attr:`nivel`.

        Só pode ser chamada a partir de uma calibração do nível 0
        (resolução plena); partir de um nível já reduzido aplicaria a
        escala duas vezes.

        Levanta
        -------
        ErroCalibracao
            Se esta calibração não for do nível 0.
        """
        if self.nivel != 0:
            raise ErroCalibracao(
                f"em_nivel() deve partir de uma calibração do nível 0, mas esta é do nível {self.nivel}."
            )
        return ParametrosCalibracao(
            micra_x=self.micra_x * nivel.fator_downsample,
            micra_y=self.micra_y * nivel.fator_downsample,
            nivel=nivel.indice,
        )

    def comprimento_pixel_x(self, pixels: float) -> Comprimento:
        """Converte um comprimento medido em pixels ao longo de X para
        um :class:`~linceu.geometria.unidades.Comprimento` físico em
        micrômetros."""
        return Comprimento(pixels * self.micra_x, UnidadeComprimento.MICROMETRO)

    def comprimento_pixel_y(self, pixels: float) -> Comprimento:
        """Converte um comprimento medido em pixels ao longo de Y para
        um :class:`~linceu.geometria.unidades.Comprimento` físico em
        micrômetros."""
        return Comprimento(pixels * self.micra_y, UnidadeComprimento.MICROMETRO)

    def pixels_x(self, comprimento: Comprimento) -> float:
        """Converte um :class:`~linceu.geometria.unidades.Comprimento`
        físico para um número de pixels ao longo de X (inverso de
        :meth:`comprimento_pixel_x`)."""
        micrometros = comprimento.converter_para(UnidadeComprimento.MICROMETRO).valor
        return micrometros / self.micra_x

    def pixels_y(self, comprimento: Comprimento) -> float:
        """Converte um :class:`~linceu.geometria.unidades.Comprimento`
        físico para um número de pixels ao longo de Y (inverso de
        :meth:`comprimento_pixel_y`)."""
        micrometros = comprimento.converter_para(UnidadeComprimento.MICROMETRO).valor
        return micrometros / self.micra_y

    def area_pixel(self, largura_px: float, altura_px: float) -> Area:
        """Converte uma região retangular em pixels para uma
        :class:`~linceu.geometria.unidades.Area` física em micrômetros
        quadrados.

        .. math::
            A = (l_{px} \\cdot micra_x) \\times (a_{px} \\cdot micra_y)
        """
        largura_um = largura_px * self.micra_x
        altura_um = altura_px * self.micra_y
        return Area(largura_um * altura_um, UnidadeArea.MICROMETRO_QUADRADO)

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"ParametrosCalibracao(micra=({self.micra_x:g},{self.micra_y:g}), nivel={self.nivel})"


def calibrar(metadados: MetadadosScanner) -> ParametrosCalibracao:
    """Função de fábrica que produz :class:`ParametrosCalibracao` a
    partir de metadados de scanner. Mantida como função livre (em vez
    de exigir que os chamadores conheçam o classmethod) para
    corresponder à responsabilidade de "calibrar parâmetros de
    aquisição" do módulo ``scanner``, como uma operação autônoma em
    forma de verbo.
    """
    return ParametrosCalibracao.a_partir_de_metadados(metadados)
