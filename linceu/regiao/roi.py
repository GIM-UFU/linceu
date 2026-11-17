"""
linceu.regiao.roi
====================

Deriva uma Região de Interesse (ROI) retangular — uma
:class:`~linceu.scanner.imagem.ImagemDigital` posicionada — a partir
de um :class:`~linceu.regiao.campo_equivalente.CampoEquivalente`
circular, delimitando-o pela sua caixa envolvente quadrada.

A ROI resultante é o formato de entrada esperado por
:meth:`linceu.es.tiff.LeitorTiff.ler_regiao` para efetivamente extrair
os pixels correspondentes da imagem de origem.
"""

from __future__ import annotations

import math

from linceu.regiao.campo_equivalente import CampoEquivalente
from linceu.scanner.imagem import ImagemDigital
from linceu.utilitarios.excecoes import ErroRegiaoInvalida


def _sem_ruido(valor: float) -> float:
    """Remove ruído de ponto flutuante (ex.: ``1559.9999999999999``) antes
    de ``floor``/``ceil``, para que um limite que é inteiro na prática
    não ganhe um pixel extra."""
    return round(valor, 6)


def calcular_roi(campo: CampoEquivalente, nivel: int | None = None) -> ImagemDigital:
    """Calcula a caixa delimitadora quadrada que circunscreve o campo
    circular ``campo``, como uma
    :class:`~linceu.scanner.imagem.ImagemDigital` posicionada e pronta
    para extração de pixels.

    A caixa é arredondada **para fora** (``floor`` no canto superior
    esquerdo, ``ceil`` no inferior direito), de modo que o círculo
    inteiro sempre cabe nela. Seu lado cobre o maior entre os diâmetros
    em X e Y do campo (relevante quando ``micra_x != micra_y``). A ROI
    é o quadrado, **sem máscara circular**: os pixels dos cantos, fora
    do círculo, fazem parte do array extraído.

    Parâmetros
    ----------
    campo:
        O campo equivalente cuja caixa envolvente será calculada. O
        nível de pirâmide da ROI é o de ``campo.calibracao.nivel``.
    nivel:
        Opcional. Se informado, deve coincidir com
        ``campo.calibracao.nivel``; serve apenas como verificação
        explícita.

    Retorna
    -------
    ImagemDigital
        Uma região posicionada, com ``x_px``/``y_px`` no canto
        superior esquerdo da caixa e ``largura_px``/``altura_px``
        iguais entre si (quadrado).

    Levanta
    -------
    ErroRegiaoInvalida
        Se ``nivel`` for informado e divergir do nível da calibração do
        campo, ou se a caixa resultante tivesse coordenadas negativas —
        ou seja, se o campo, centrado em ``centro_px``, se estendesse
        além da borda superior/esquerda da imagem. Extensão além da
        borda inferior/direita só é detectável na leitura (conhecer o
        tamanho da imagem), e é verificada por
        :meth:`linceu.es.tiff.LeitorTiff.ler_regiao`.
    """
    nivel_campo = campo.calibracao.nivel
    if nivel is not None and nivel != nivel_campo:
        raise ErroRegiaoInvalida(
            f"nivel={nivel} diverge do nível da calibração do campo ({nivel_campo}); "
            f"use a calibração do nível desejado (ParametrosCalibracao.em_nivel)."
        )

    lado_px = max(campo.diametro_px, campo.calibracao.pixels_y(campo.diametro))
    raio_px = lado_px / 2.0

    x0 = math.floor(_sem_ruido(campo.centro_x_px - raio_px))
    y0 = math.floor(_sem_ruido(campo.centro_y_px - raio_px))
    x1 = math.ceil(_sem_ruido(campo.centro_x_px + raio_px))
    y1 = math.ceil(_sem_ruido(campo.centro_y_px + raio_px))

    if x0 < 0 or y0 < 0:
        raise ErroRegiaoInvalida(
            f"O campo centrado em {campo.centro_px} com diâmetro {lado_px:.1f}px "
            f"se estende além da borda superior/esquerda da imagem "
            f"(caixa calculada em ({x0},{y0}))."
        )

    lado = max(x1 - x0, y1 - y0)
    return ImagemDigital(
        largura_px=lado,
        altura_px=lado,
        calibracao=campo.calibracao,
        x_px=x0,
        y_px=y0,
        nivel=nivel_campo,
        rotulo="roi_campo_equivalente",
    )
