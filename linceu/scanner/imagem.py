"""
linceu.scanner.imagem
========================

``ImagemDigital`` representa uma região de imagem digital fisicamente
calibrada — seja uma lâmina inteira ou uma sub-região arbitrária (uma
região de interesse recortada de um nível específico da pirâmide).
Ela satisfaz o protocolo :class:`~linceu.geometria.campo.TemArea`, o
que é o que permite que seja usada diretamente pelos cálculos de campo
equivalente em :mod:`linceu.regiao`.
"""

from __future__ import annotations

from dataclasses import dataclass

from linceu.geometria.unidades import Area
from linceu.scanner.calibracao import ParametrosCalibracao, calibrar
from linceu.scanner.metadados import MetadadosScanner
from linceu.utilitarios.excecoes import ErroRegiaoInvalida
from linceu.utilitarios.validacao import exigir_inteiro_nao_negativo, exigir_inteiro_positivo


@dataclass(frozen=True, slots=True)
class ImagemDigital:
    """Uma região de imagem digital imutável e fisicamente calibrada.

    Parâmetros
    ----------
    largura_px, altura_px:
        Dimensões em pixels da região, no nível de pirâmide indicado
        por :attr:`nivel`.
    calibracao:
        Os :class:`~linceu.scanner.calibracao.ParametrosCalibracao`
        usados para converter pixels em unidades físicas, já
        referentes ao nível indicado por :attr:`nivel` (veja
        :meth:`~linceu.scanner.calibracao.ParametrosCalibracao.em_nivel`).
        Seu ``nivel`` deve coincidir com :attr:`nivel`.
    x_px, y_px:
        Deslocamento do canto superior esquerdo desta região, em
        pixels, relativo à origem da imagem completa no mesmo nível de
        pirâmide. ``(0, 0)`` para a lâmina inteira.
    nivel:
        Índice do nível de pirâmide (0 = resolução plena) ao qual
        ``largura_px``/``altura_px``/``x_px``/``y_px`` se referem.
    rotulo:
        Identificador opcional (ex.: um ID de lâmina ou nome de ROI).

    Invariantes
    ------------
    * ``largura_px > 0`` e ``altura_px > 0``.
    * ``x_px >= 0``, ``y_px >= 0``, ``nivel >= 0``.
    * ``calibracao.nivel == nivel``.
    """

    largura_px: int
    altura_px: int
    calibracao: ParametrosCalibracao
    x_px: int = 0
    y_px: int = 0
    nivel: int = 0
    rotulo: str | None = None

    def __post_init__(self) -> None:
        exigir_inteiro_positivo(self.largura_px, "ImagemDigital.largura_px", excecao=ErroRegiaoInvalida)
        exigir_inteiro_positivo(self.altura_px, "ImagemDigital.altura_px", excecao=ErroRegiaoInvalida)
        exigir_inteiro_nao_negativo(self.x_px, "ImagemDigital.x_px", excecao=ErroRegiaoInvalida)
        exigir_inteiro_nao_negativo(self.y_px, "ImagemDigital.y_px", excecao=ErroRegiaoInvalida)
        exigir_inteiro_nao_negativo(self.nivel, "ImagemDigital.nivel", excecao=ErroRegiaoInvalida)
        if self.calibracao.nivel != self.nivel:
            raise ErroRegiaoInvalida(
                f"ImagemDigital.nivel={self.nivel} é inconsistente com a calibração, "
                f"que se refere ao nível {self.calibracao.nivel}."
            )

    @property
    def area(self) -> Area:
        """Área física desta região de imagem, em micrômetros quadrados."""
        return self.calibracao.area_pixel(self.largura_px, self.altura_px)

    @property
    def caixa_pixels(self) -> tuple[int, int, int, int]:
        """A caixa delimitadora desta região como ``(x0, y0, x1, y1)``,
        em pixels, no seu nível de pirâmide — a forma esperada por
        leitores de :mod:`linceu.es` para extração de pixels."""
        return (self.x_px, self.y_px, self.x_px + self.largura_px, self.y_px + self.altura_px)

    @classmethod
    def lamina_inteira(
        cls, metadados: MetadadosScanner, nivel: int = 0, rotulo: str | None = None
    ) -> ImagemDigital:
        """Constrói uma :class:`ImagemDigital` cobrindo toda a extensão
        de uma lâmina escaneada em um dado nível de pirâmide, derivando
        a calibração diretamente de seus
        :class:`~linceu.scanner.metadados.MetadadosScanner`.
        """
        nivel_piramide = metadados.nivel(nivel)
        calibracao_nivel = calibrar(metadados).em_nivel(nivel_piramide)
        return cls(
            largura_px=nivel_piramide.largura_px,
            altura_px=nivel_piramide.altura_px,
            calibracao=calibracao_nivel,
            nivel=nivel,
            rotulo=rotulo,
        )

    def sub_regiao(
        self, x_px: int, y_px: int, largura_px: int, altura_px: int, rotulo: str | None = None
    ) -> ImagemDigital:
        """Constrói uma nova :class:`ImagemDigital` representando uma
        região menor (ex.: uma região de interesse) dentro desta
        imagem, posicionada em ``(x_px, y_px)`` relativo à origem desta
        imagem e usando a mesma calibração e nível de pirâmide.
        """
        return ImagemDigital(
            largura_px=largura_px,
            altura_px=altura_px,
            calibracao=self.calibracao,
            x_px=self.x_px + x_px,
            y_px=self.y_px + y_px,
            nivel=self.nivel,
            rotulo=rotulo,
        )

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        tag = f" [{self.rotulo}]" if self.rotulo else ""
        return (
            f"ImagemDigital({self.largura_px}x{self.altura_px}px @ "
            f"({self.x_px},{self.y_px}) nivel={self.nivel}, area={self.area!r}){tag}"
        )
