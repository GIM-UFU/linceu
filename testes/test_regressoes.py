"""Testes de regressão para os problemas encontrados na revisão pré-publicação:

* leitura de regiões sem decodificar o nível inteiro (memória limitada);
* consistência entre o nível de pirâmide e a calibração;
* arredondamento "para fora" da ROI (o círculo sempre cabe na caixa);
* formatos/arquivos incomuns (strips, JPEG, planos separados, corrompido).
"""

import tracemalloc

import numpy as np
import pytest
import tifffile

from linceu import (
    ErroCalibracao,
    ErroFormatoNaoSuportado,
    ErroRegiaoInvalida,
    ImagemDigital,
    LeitorTiff,
    Microscopio,
    NivelPiramide,
    Objetiva,
    Ocular,
    ParametrosCalibracao,
    calcular_campo_equivalente,
    calcular_roi,
    calibrar,
)


@pytest.fixture
def cor_padrao():
    return Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0)).campo_optico_referencia


def _gradiente(altura: int, largura: int) -> np.ndarray:
    """Imagem RGB determinística e muito compressível (arquivos pequenos)."""
    y = np.arange(altura, dtype=np.uint32)[:, None]
    x = np.arange(largura, dtype=np.uint32)[None, :]
    canais = [(x // 16) % 256, (y // 16) % 256, ((x + y) // 32) % 256]
    return np.stack([np.broadcast_to(c, (altura, largura)) for c in canais], axis=-1).astype(np.uint8)


# --------------------------------------------------------------------------
# Leitura por tiles: memória proporcional à região, não à lâmina
# --------------------------------------------------------------------------
def test_ler_regiao_nao_decodifica_o_nivel_inteiro(tmp_path):
    altura, largura = 6000, 6000  # 108 MB descomprimidos
    caminho = str(tmp_path / "grande.btf")
    base = _gradiente(altura, largura)
    tifffile.imwrite(
        caminho,
        base,
        bigtiff=True,
        tile=(256, 256),
        compression="deflate",
        photometric="rgb",
        resolution=(1e4 / 0.25, 1e4 / 0.25),
        resolutionunit="CENTIMETER",
    )
    leitor = LeitorTiff()
    calibracao = calibrar(leitor.ler_metadados(caminho))
    roi = ImagemDigital(largura_px=300, altura_px=300, calibracao=calibracao, x_px=3000, y_px=2500)

    tracemalloc.start()
    try:
        pixels = leitor.ler_regiao(caminho, roi)
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert np.array_equal(pixels, base[2500:2800, 3000:3300])
    # a lâmina inteira ocupa ~108 MB; a leitura por tiles deve ficar ordens de grandeza abaixo
    assert pico < 10_000_000, f"pico de memória alto demais: {pico / 1e6:.1f} MB"


def test_ler_regiao_em_tiff_por_strips_e_sem_piramide(tmp_path):
    caminho = str(tmp_path / "strips.tif")
    base = _gradiente(500, 700)
    tifffile.imwrite(caminho, base, photometric="rgb", resolution=(4000, 4000), resolutionunit="CENTIMETER")
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho)
    assert not metadados.eh_piramidal

    roi = ImagemDigital.lamina_inteira(metadados).sub_regiao(100, 50, 200, 120)
    assert np.array_equal(leitor.ler_regiao(caminho, roi), base[50:170, 100:300])


def test_ler_regiao_em_tons_de_cinza(tmp_path):
    caminho = str(tmp_path / "cinza.tif")
    base = _gradiente(300, 300)[..., 0]
    tifffile.imwrite(caminho, base, resolution=(4000, 4000), resolutionunit="CENTIMETER")
    leitor = LeitorTiff()
    roi = ImagemDigital.lamina_inteira(leitor.ler_metadados(caminho)).sub_regiao(10, 20, 50, 40)
    pixels = leitor.ler_regiao(caminho, roi)
    assert pixels.shape == (40, 50)
    assert np.array_equal(pixels, base[20:60, 10:60])


def test_ler_regiao_tiles_jpeg_exigem_e_usam_imagecodecs(tmp_path):
    """Lâminas reais costumam ter tiles JPEG; isso depende de ``imagecodecs``."""
    caminho = str(tmp_path / "jpeg.tif")
    base = _gradiente(512, 512)
    tifffile.imwrite(
        caminho,
        base,
        tile=(256, 256),
        compression="jpeg",
        photometric="rgb",
        resolution=(4000, 4000),
        resolutionunit="CENTIMETER",
    )
    leitor = LeitorTiff()
    roi = ImagemDigital.lamina_inteira(leitor.ler_metadados(caminho)).sub_regiao(0, 0, 256, 256)
    pixels = leitor.ler_regiao(caminho, roi)
    assert pixels.shape == (256, 256, 3)
    # JPEG é com perdas: aceita-se erro médio pequeno
    assert np.abs(pixels.astype(int) - base[:256, :256].astype(int)).mean() < 8


def test_ler_regiao_planos_separados_nao_suportado(tmp_path):
    caminho = str(tmp_path / "planar.tif")
    base = _gradiente(100, 100)
    tifffile.imwrite(
        caminho,
        base,
        photometric="rgb",
        planarconfig="separate",
        resolution=(4000, 4000),
        resolutionunit="CENTIMETER",
    )
    leitor = LeitorTiff()
    roi = ImagemDigital.lamina_inteira(leitor.ler_metadados(caminho)).sub_regiao(0, 0, 10, 10)
    with pytest.raises(ErroFormatoNaoSuportado):
        leitor.ler_regiao(caminho, roi)


def test_arquivo_corrompido_levanta_erro_do_dominio(tmp_path):
    caminho = tmp_path / "lixo.tif"
    caminho.write_bytes(b"isto nao e um TIFF")
    leitor = LeitorTiff()
    with pytest.raises(ErroFormatoNaoSuportado):
        leitor.ler_metadados(str(caminho))
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    with pytest.raises(ErroFormatoNaoSuportado):
        leitor.ler_regiao(str(caminho), ImagemDigital(10, 10, calibracao))


def test_arquivo_inexistente_levanta_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        LeitorTiff().ler_metadados(str(tmp_path / "nao_existe.tif"))


def test_extensao_nao_suportada_levanta_erro(tmp_path):
    with pytest.raises(ErroFormatoNaoSuportado):
        LeitorTiff().ler_metadados(str(tmp_path / "lamina.svs"))


# --------------------------------------------------------------------------
# Nível de pirâmide consistente com a calibração
# --------------------------------------------------------------------------
NIVEL_2 = NivelPiramide(indice=2, largura_px=250, altura_px=250, fator_downsample=4.0)


def test_imagem_digital_com_nivel_inconsistente_levanta_erro():
    calibracao_nivel0 = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    with pytest.raises(ErroRegiaoInvalida):
        ImagemDigital(largura_px=10, altura_px=10, calibracao=calibracao_nivel0, nivel=2)


def test_calcular_roi_herda_nivel_da_calibracao(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25).em_nivel(NIVEL_2)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=200, centro_y_px=200)
    assert calcular_roi(campo).nivel == 2


def test_calcular_roi_com_nivel_divergente_levanta_erro(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25).em_nivel(NIVEL_2)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=200, centro_y_px=200)
    with pytest.raises(ErroRegiaoInvalida):
        calcular_roi(campo, nivel=0)
    assert calcular_roi(campo, nivel=2).nivel == 2


def test_em_nivel_so_parte_do_nivel_zero():
    calibracao_nivel2 = ParametrosCalibracao(micra_x=0.25, micra_y=0.25).em_nivel(NIVEL_2)
    with pytest.raises(ErroCalibracao):
        calibracao_nivel2.em_nivel(NIVEL_2)


def test_fluxo_completo_em_nivel_reduzido(tmp_path, cor_padrao):
    caminho = str(tmp_path / "piramide.btf")
    base = _gradiente(4096, 4096)
    opcoes = dict(
        tile=(256, 256),
        photometric="rgb",
        resolution=(1e4 / 0.25, 1e4 / 0.25),
        resolutionunit="CENTIMETER",
    )
    with tifffile.TiffWriter(caminho, bigtiff=True) as tw:
        tw.write(base, subifds=1, **opcoes)
        tw.write(base[::2, ::2], subfiletype=1, **opcoes)
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho)
    calibracao = calibrar(metadados).em_nivel(metadados.nivel(1))

    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=1000, centro_y_px=1000)
    roi = calcular_roi(campo)
    assert roi.nivel == 1
    nivel1 = base[::2, ::2]
    x0, y0, x1, y1 = roi.caixa_pixels
    assert np.array_equal(leitor.ler_regiao(caminho, roi), nivel1[y0:y1, x0:x1])


# --------------------------------------------------------------------------
# ROI arredondada para fora: o círculo sempre cabe
# --------------------------------------------------------------------------
def test_roi_nao_ganha_pixel_extra_por_ruido_de_ponto_flutuante(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=2000, centro_y_px=2000)
    roi = calcular_roi(campo)
    assert (roi.x_px, roi.y_px, roi.largura_px, roi.altura_px) == (1560, 1560, 880, 880)


@pytest.mark.parametrize("micra", [(0.25, 0.25), (0.2527, 0.2527), (0.25, 0.31), (0.499, 0.25)])
@pytest.mark.parametrize("centro", [(2000.0, 2000.0), (1234.56, 987.65), (1500.5, 3000.25)])
def test_roi_sempre_contem_o_circulo_inteiro(cor_padrao, micra, centro):
    calibracao = ParametrosCalibracao(micra_x=micra[0], micra_y=micra[1])
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=centro[0], centro_y_px=centro[1])
    roi = calcular_roi(campo)
    x0, y0, x1, y1 = roi.caixa_pixels
    raio_x = campo.diametro_px / 2
    raio_y = calibracao.pixels_y(campo.diametro) / 2
    assert x0 <= centro[0] - raio_x and centro[0] + raio_x <= x1
    assert y0 <= centro[1] - raio_y and centro[1] + raio_y <= y1
    assert roi.largura_px == roi.altura_px
