"""
linceu.scanner.metadados
===========================

Objetos de valor imutáveis que descrevem os parâmetros de aquisição de
um scanner de lâminas digitais (Whole Slide Imaging), independentemente
de qualquer formato de arquivo específico.

:class:`NivelPiramide` descreve um único nível da pirâmide de
resoluções de uma imagem piramidal (comum em WSI: a imagem é
armazenada em múltiplas resoluções, da mais fina — nível 0 — à mais
grosseira, para permitir navegação e visualização eficientes).
:class:`MetadadosScanner` agrega a resolução física (micra por pixel),
as dimensões e a pirâmide de níveis de uma aquisição.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from linceu.utilitarios.excecoes import ErroCalibracao
from linceu.utilitarios.validacao import (
    exigir_inteiro_nao_negativo,
    exigir_inteiro_positivo,
    exigir_positivo,
    exigir_string_nao_vazia,
)


@dataclass(frozen=True, slots=True)
class NivelPiramide:
    """Um único nível de resolução de uma imagem piramidal.

    Parâmetros
    ----------
    indice:
        Posição deste nível na pirâmide, ``0`` sendo a resolução mais
        fina (imagem em tamanho real).
    largura_px, altura_px:
        Dimensões deste nível, em pixels.
    fator_downsample:
        Fator de redução de escala deste nível em relação ao nível 0
        (ex.: ``4.0`` significa que este nível tem 1/4 da resolução
        linear do nível base). Sempre ``>= 1.0``.

    Invariantes
    ------------
    * ``indice >= 0``
    * ``largura_px > 0`` e ``altura_px > 0``
    * ``fator_downsample >= 1.0``
    """

    indice: int
    largura_px: int
    altura_px: int
    fator_downsample: float

    def __post_init__(self) -> None:
        exigir_inteiro_nao_negativo(self.indice, "NivelPiramide.indice", excecao=ErroCalibracao)
        exigir_inteiro_positivo(self.largura_px, "NivelPiramide.largura_px", excecao=ErroCalibracao)
        exigir_inteiro_positivo(self.altura_px, "NivelPiramide.altura_px", excecao=ErroCalibracao)
        if self.fator_downsample < 1.0:
            raise ErroCalibracao(
                f"NivelPiramide.fator_downsample deve ser >= 1.0, recebido {self.fator_downsample!r}."
            )

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (
            f"NivelPiramide(indice={self.indice}, "
            f"{self.largura_px}x{self.altura_px}px, "
            f"downsample={self.fator_downsample:g}x)"
        )


@dataclass(frozen=True, slots=True)
class MetadadosScanner:
    """Descrição neutra em relação a fabricante de uma aquisição de
    imagem de lâmina inteira (WSI).

    Parâmetros
    ----------
    micra_x, micra_y:
        Resolução em micra por pixel ao longo dos eixos X e Y, no
        nível 0 (resolução plena) da pirâmide. A maioria dos scanners
        reporta valores quase idênticos para ambos os eixos; ambos são
        mantidos explicitamente em vez de assumir isotropia, já que
        pixels não quadrados de fato ocorrem.
    largura_px, altura_px:
        Dimensões da imagem em resolução plena (nível 0), em pixels.
    niveis:
        Tupla ordenada de :class:`NivelPiramide` descrevendo cada
        resolução disponível na pirâmide, do nível 0 em diante. Uma
        imagem não piramidal (TIFF de página única) é modelada como
        uma pirâmide de um único nível.
    fabricante:
        Fabricante do scanner em texto livre (ex.: ``"Hamamatsu"``,
        ``"Leica"``, ``"Aperio"``). Usado apenas para proveniência.
    potencia_objetiva:
        A ampliação nominal da objetiva usada durante a aquisição, se
        reportada pelo scanner.

    Invariantes
    ------------
    * ``micra_x > 0`` e ``micra_y > 0``
    * ``largura_px > 0`` e ``altura_px > 0`` (inteiros positivos)
    * ``niveis`` não vazio, e ``niveis[0].indice == 0``
    """

    micra_x: float
    micra_y: float
    largura_px: int
    altura_px: int
    niveis: tuple[NivelPiramide, ...] = field(default=())
    fabricante: str = "desconhecido"
    potencia_objetiva: float | None = None

    def __post_init__(self) -> None:
        exigir_positivo(self.micra_x, "MetadadosScanner.micra_x", excecao=ErroCalibracao)
        exigir_positivo(self.micra_y, "MetadadosScanner.micra_y", excecao=ErroCalibracao)
        exigir_inteiro_positivo(self.largura_px, "MetadadosScanner.largura_px", excecao=ErroCalibracao)
        exigir_inteiro_positivo(self.altura_px, "MetadadosScanner.altura_px", excecao=ErroCalibracao)
        exigir_string_nao_vazia(self.fabricante, "MetadadosScanner.fabricante", excecao=ErroCalibracao)
        if self.potencia_objetiva is not None:
            exigir_positivo(
                self.potencia_objetiva, "MetadadosScanner.potencia_objetiva", excecao=ErroCalibracao
            )

        if not self.niveis:
            # Nenhuma pirâmide foi informada: modela a imagem como uma
            # pirâmide degenerada de um único nível (o próprio nível 0),
            # de modo que `niveis` nunca esteja vazio para o código
            # cliente que percorre a pirâmide.
            object.__setattr__(
                self,
                "niveis",
                (
                    NivelPiramide(
                        indice=0, largura_px=self.largura_px, altura_px=self.altura_px, fator_downsample=1.0
                    ),
                ),
            )
        elif self.niveis[0].indice != 0:
            raise ErroCalibracao("MetadadosScanner.niveis deve começar no índice 0 (resolução plena).")

    @property
    def eh_isotropico(self) -> bool:
        """Se os passos de pixel em X e Y são iguais (dentro da
        tolerância de ponto flutuante)."""
        return abs(self.micra_x - self.micra_y) < 1e-9

    @property
    def eh_piramidal(self) -> bool:
        """Se esta aquisição possui mais de um nível de resolução."""
        return len(self.niveis) > 1

    def nivel(self, indice: int) -> NivelPiramide:
        """Retorna o :class:`NivelPiramide` de índice ``indice``.

        Levanta
        -------
        ErroCalibracao
            Se não existir nenhum nível com esse índice.
        """
        for nivel in self.niveis:
            if nivel.indice == indice:
                return nivel
        raise ErroCalibracao(
            f"Nível de pirâmide {indice} inexistente; níveis disponíveis: {[n.indice for n in self.niveis]}."
        )

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (
            f"MetadadosScanner(fabricante={self.fabricante!r}, "
            f"micra=({self.micra_x:g},{self.micra_y:g}), "
            f"dims={self.largura_px}x{self.altura_px}px, "
            f"niveis={len(self.niveis)})"
        )
