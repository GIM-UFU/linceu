"""
Script de verificação autônomo para o pacote `linceu`.

Exercita todas as camadas da biblioteca (geometria, microscopia,
scanner, es, regiao) usando uma lâmina TIFF sintética gerada em tempo
de execução, e confere os resultados contra valores esperados
calculados manualmente, usando math.isclose. Execute com:

    python verificar.py

Termina com status 0 e imprime "TODAS AS VERIFICAÇÕES PASSARAM" se
tudo estiver correto; levanta AssertionError com uma mensagem
descritiva caso contrário.

Requer as dependências do projeto instaladas (tifffile, numpy), já
que, ao contrário do antigo script equivalente do framework original,
esta biblioteca lê arquivos de imagem de verdade — não há como
verificar a camada de E/S sem elas.
"""

from __future__ import annotations

import math
import os
import sys
import tempfile

from linceu import (
    ImagemDigital,
    LeitorTiff,
    Microscopio,
    Objetiva,
    Ocular,
    calcular_campo_equivalente,
    calcular_roi,
    calibrar,
    converter_coordenada,
)


def _gerar_lamina_sintetica(caminho: str) -> None:
    import numpy as np
    import tifffile

    base = (np.random.rand(1024, 1024, 3) * 255).astype("uint8")
    niveis = [base, base[::2, ::2], base[::4, ::4]]
    with tifffile.TiffWriter(caminho, bigtiff=True) as tif:
        tif.write(
            niveis[0],
            tile=(256, 256),
            resolution=(1e4 / 0.25, 1e4 / 0.25),
            resolutionunit="CENTIMETER",
            description="Verificacao |MPP = 0.2500",
            subifds=len(niveis) - 1,
        )
        for nivel in niveis[1:]:
            tif.write(
                nivel,
                tile=(256, 256),
                resolution=(1e4 / 0.25, 1e4 / 0.25),
                resolutionunit="CENTIMETER",
                subfiletype=1,
            )


def principal() -> None:
    with tempfile.TemporaryDirectory() as diretorio_temp:
        caminho = os.path.join(diretorio_temp, "lamina.btf")
        _gerar_lamina_sintetica(caminho)

        # --- microscopia -------------------------------------------------
        escopo = Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0))
        cor = escopo.campo_optico_referencia
        assert math.isclose(cor.diametro.valor, 0.22, rel_tol=1e-9), "Diâmetro do COR incorreto"
        assert math.isclose(cor.area.valor, math.pi * (0.11**2), rel_tol=1e-9), "Área do COR incorreta"

        # --- es (leitura TIFF/BigTIFF) ------------------------------------
        leitor = LeitorTiff()
        assert leitor.suporta(caminho), "LeitorTiff deveria suportar .btf"
        metadados = leitor.ler_metadados(caminho)
        assert math.isclose(metadados.micra_x, 0.25, rel_tol=1e-3), "MPP lido incorretamente"
        assert metadados.largura_px == 1024 and metadados.altura_px == 1024
        assert metadados.eh_piramidal and len(metadados.niveis) == 3, "Pirâmide não detectada corretamente"

        # --- scanner: calibração e conversões -----------------------------
        calibracao = calibrar(metadados)
        assert math.isclose(calibracao.pixels_x(calibracao.comprimento_pixel_x(40.0)), 40.0, rel_tol=1e-9)

        n0 = metadados.nivel(0)
        n1 = metadados.nivel(1)
        x1, _ = converter_coordenada(200, 200, n0, n1)
        assert math.isclose(x1, 100.0, rel_tol=1e-9), "Conversão entre níveis de pirâmide incorreta"

        # --- regiao: campo equivalente e ROI ------------------------------
        campo = calcular_campo_equivalente(cor, calibracao, centro_x_px=500, centro_y_px=500)
        diametro_px_esperado = (0.22 * 1000.0) / 0.25  # mm -> um -> px
        assert math.isclose(campo.diametro_px, diametro_px_esperado, rel_tol=1e-6), (
            "Campo equivalente incorreto"
        )

        roi = calcular_roi(campo)
        assert roi.largura_px == roi.altura_px, "ROI deveria ser quadrada"
        x0, y0, x1_, y1_ = roi.caixa_pixels
        assert x0 <= 500 <= x1_ and y0 <= 500 <= y1_, "Centro do campo fora da ROI calculada"

        # --- extração de pixels de fato ------------------------------------
        pixels = leitor.ler_regiao(caminho, roi)
        assert pixels.shape == (roi.altura_px, roi.largura_px, 3), "Forma dos pixels extraídos incorreta"

        # --- sub-regiões e níveis de pirâmide -------------------------------
        imagem_inteira = ImagemDigital.lamina_inteira(metadados)
        assert imagem_inteira.largura_px == 1024
        sub = imagem_inteira.sub_regiao(10, 10, 50, 50)
        assert sub.x_px == 10 and sub.largura_px == 50

    print("TODAS AS VERIFICAÇÕES PASSARAM")


if __name__ == "__main__":
    try:
        principal()
    except AssertionError as erro:
        print(f"FALHA NA VERIFICAÇÃO: {erro}", file=sys.stderr)
        sys.exit(1)
