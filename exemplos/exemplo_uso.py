"""
Exemplo de uso da biblioteca ``linceu``.

Demonstra o fluxo completo de infraestrutura oferecido pela biblioteca:

    1. Ler os metadados (resolução, dimensões, pirâmide) de uma lâmina
       TIFF/BigTIFF.
    2. Definir a configuração óptica de um microscópio e obter seu
       Campo Óptico de Referência (COR).
    3. Calibrar a imagem do scanner a partir dos metadados lidos.
    4. Calcular o campo equivalente do microscópio projetado sobre um
       ponto da imagem do scanner.
    5. Derivar a Região de Interesse (ROI) retangular correspondente.
    6. Extrair os pixels dessa ROI diretamente do arquivo.

Este script gera uma lâmina sintética em ``/tmp`` apenas para fins de
demonstração; substitua ``caminho_lamina`` por um arquivo real
(``.tif``/``.tiff``/``.btf``) para uso em produção.

A biblioteca não faz nenhuma análise sobre os pixels extraídos — o que
fazer com ``pixels_roi`` (detecção, classificação, contagem, etc.) é
responsabilidade de código de protocolo construído por cima dela.
"""

from __future__ import annotations

from linceu import (
    LeitorTiff,
    Microscopio,
    Objetiva,
    Ocular,
    calcular_campo_equivalente,
    calcular_roi,
    calibrar,
)


def _gerar_lamina_sintetica(caminho: str) -> None:
    """Cria uma lâmina BigTIFF piramidal sintética apenas para este
    exemplo poder ser executado sem depender de um arquivo real."""
    import numpy as np
    import tifffile

    base = (np.random.rand(4096, 4096, 3) * 255).astype("uint8")
    niveis = [base, base[::2, ::2], base[::4, ::4]]
    with tifffile.TiffWriter(caminho, bigtiff=True) as tif:
        tif.write(
            niveis[0],
            tile=(256, 256),
            resolution=(1e4 / 0.25, 1e4 / 0.25),
            resolutionunit="CENTIMETER",
            description="Lamina sintetica de exemplo |MPP = 0.2500",
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


def main() -> None:
    caminho_lamina = "/tmp/exemplo_linceu/lamina.btf"

    import os

    os.makedirs(os.path.dirname(caminho_lamina), exist_ok=True)
    if not os.path.exists(caminho_lamina):
        _gerar_lamina_sintetica(caminho_lamina)

    # 1. Lê os metadados da lâmina.
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho_lamina)
    print(f"Metadados: {metadados}")
    print(f"Níveis de pirâmide: {[n.indice for n in metadados.niveis]}")

    # 2. Define a configuração óptica do microscópio (100x, ocular FN22)
    #    e obtém seu Campo Óptico de Referência.
    escopo = Microscopio(
        ocular=Ocular(numero_campo=22.0, ampliacao=10.0),
        objetiva=Objetiva(ampliacao=100.0),
        nome="Microscópio do laboratório",
    )
    cor = escopo.campo_optico_referencia
    print(f"Campo Óptico de Referência: diâmetro={cor.diametro!r}, área={cor.area!r}")

    # 3. Calibra a imagem do scanner a partir dos metadados lidos.
    calibracao = calibrar(metadados)

    # 4. Calcula o campo equivalente do microscópio centrado em um
    #    ponto arbitrário da imagem do scanner (ex.: um ponto de
    #    interesse escolhido por um protocolo externo).
    centro_x_px, centro_y_px = 2000.0, 2000.0
    campo = calcular_campo_equivalente(cor, calibracao, centro_x_px, centro_y_px)
    print(f"Campo equivalente: {campo}")
    print(f"  diâmetro em pixels: {campo.diametro_px:.1f}px")
    print(f"  área em pixels: {campo.area_px!r}")

    # 5. Deriva a ROI retangular que circunscreve o campo circular.
    roi = calcular_roi(campo)
    print(f"ROI calculada: {roi}")

    # 6. Extrai os pixels dessa ROI diretamente do arquivo TIFF/BigTIFF.
    pixels_roi = leitor.ler_regiao(caminho_lamina, roi)
    print(f"Pixels extraídos: shape={pixels_roi.shape}, dtype={pixels_roi.dtype}")


if __name__ == "__main__":
    main()
