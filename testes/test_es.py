"""Testes unitários para linceu.es.tiff.LeitorTiff.

Gera arquivos TIFF/BigTIFF sintéticos e piramidais em tempo de teste
(via ``tifffile``) para não depender de nenhum arquivo de lâmina real
como fixture binária.
"""

import numpy as np
import pytest
import tifffile

from linceu.es.tiff import EXTENSOES_SUPORTADAS, LeitorTiff
from linceu.scanner import ImagemDigital, ParametrosCalibracao, calibrar
from linceu.utilitarios.excecoes import ErroCalibracao, ErroFormatoNaoSuportado, ErroRegiaoInvalida


@pytest.fixture
def lamina_piramidal_aperio(tmp_path):
    """Um BigTIFF piramidal de 3 níveis com MPP embutido em ImageDescription
    (estilo Aperio), como comumente encontrado em lâminas reais."""
    caminho = tmp_path / "lamina.btf"
    base = (np.random.rand(1024, 1024, 3) * 255).astype("uint8")
    niveis = [base, base[::2, ::2], base[::4, ::4]]
    with tifffile.TiffWriter(str(caminho), bigtiff=True) as tif:
        tif.write(
            niveis[0],
            tile=(256, 256),
            resolution=(1e4 / 0.25, 1e4 / 0.25),
            resolutionunit="CENTIMETER",
            description="Aperio Image Library |AppMag = 40|MPP = 0.2500",
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
    return str(caminho), niveis


@pytest.fixture
def lamina_simples_sem_mpp(tmp_path):
    """Um TIFF não piramidal, com resolução apenas via
    XResolution/YResolution (sem string MPP)."""
    caminho = tmp_path / "simples.tif"
    dados = (np.random.rand(64, 64, 3) * 255).astype("uint8")
    tifffile.imwrite(str(caminho), dados, resolution=(1e4 / 0.5, 1e4 / 0.5), resolutionunit="CENTIMETER")
    return str(caminho), dados


@pytest.fixture
def lamina_sem_resolucao(tmp_path):
    """Um TIFF sem nenhuma informação de resolução física."""
    caminho = tmp_path / "sem_resolucao.tif"
    dados = (np.random.rand(32, 32, 3) * 255).astype("uint8")
    tifffile.imwrite(str(caminho), dados)
    return str(caminho)


def test_suporta_extensoes_reconhecidas():
    leitor = LeitorTiff()
    assert leitor.suporta("/x/lamina.tif")
    assert leitor.suporta("/x/lamina.TIFF")
    assert leitor.suporta("/x/lamina.btf")
    assert not leitor.suporta("/x/lamina.svs")
    assert EXTENSOES_SUPORTADAS == {".tif", ".tiff", ".btf"}


def test_ler_metadados_extensao_nao_suportada():
    leitor = LeitorTiff()
    with pytest.raises(ErroFormatoNaoSuportado):
        leitor.ler_metadados("/x/lamina.svs")


def test_ler_metadados_piramide_e_mpp_aperio(lamina_piramidal_aperio):
    caminho, _ = lamina_piramidal_aperio
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho)

    assert metadados.micra_x == pytest.approx(0.25, rel=1e-3)
    assert metadados.micra_y == pytest.approx(0.25, rel=1e-3)
    assert metadados.largura_px == 1024
    assert metadados.altura_px == 1024
    assert metadados.fabricante == "Aperio"
    assert metadados.eh_piramidal
    assert len(metadados.niveis) == 3
    assert metadados.niveis[0].fator_downsample == pytest.approx(1.0)
    assert metadados.niveis[1].fator_downsample == pytest.approx(2.0)
    assert metadados.niveis[2].fator_downsample == pytest.approx(4.0)


def test_ler_metadados_resolucao_padrao_sem_mpp(lamina_simples_sem_mpp):
    caminho, _ = lamina_simples_sem_mpp
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho)
    assert metadados.micra_x == pytest.approx(0.5, rel=1e-3)
    assert not metadados.eh_piramidal


def test_ler_metadados_sem_resolucao_levanta_erro_calibracao(lamina_sem_resolucao):
    leitor = LeitorTiff()
    with pytest.raises(ErroCalibracao):
        leitor.ler_metadados(lamina_sem_resolucao)


def test_ler_regiao_nivel_0(lamina_piramidal_aperio):
    caminho, niveis_originais = lamina_piramidal_aperio
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho)

    roi = ImagemDigital(
        largura_px=100, altura_px=80, calibracao=calibrar(metadados), x_px=10, y_px=20, nivel=0
    )
    pixels = leitor.ler_regiao(caminho, roi)

    assert pixels.shape == (80, 100, 3)
    esperado = niveis_originais[0][20:100, 10:110]
    assert np.array_equal(pixels, esperado)


def test_ler_regiao_nivel_diferente_de_zero(lamina_piramidal_aperio):
    caminho, niveis_originais = lamina_piramidal_aperio
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho)

    calibracao_nivel1 = calibrar(metadados).em_nivel(metadados.nivel(1))
    roi = ImagemDigital(largura_px=50, altura_px=50, calibracao=calibracao_nivel1, x_px=0, y_px=0, nivel=1)
    pixels = leitor.ler_regiao(caminho, roi)

    assert pixels.shape == (50, 50, 3)
    assert np.array_equal(pixels, niveis_originais[1][0:50, 0:50])


def test_ler_regiao_fora_dos_limites_levanta_erro(lamina_piramidal_aperio):
    caminho, _ = lamina_piramidal_aperio
    leitor = LeitorTiff()
    metadados = leitor.ler_metadados(caminho)

    roi = ImagemDigital(
        largura_px=100, altura_px=100, calibracao=calibrar(metadados), x_px=1000, y_px=1000, nivel=0
    )
    with pytest.raises(ErroRegiaoInvalida):
        leitor.ler_regiao(caminho, roi)


def test_ler_regiao_nivel_inexistente_levanta_erro(lamina_piramidal_aperio):
    caminho, _ = lamina_piramidal_aperio
    leitor = LeitorTiff()

    calibracao_inexistente = ParametrosCalibracao(micra_x=0.25, micra_y=0.25, nivel=99)
    roi = ImagemDigital(largura_px=10, altura_px=10, calibracao=calibracao_inexistente, nivel=99)
    with pytest.raises(ErroRegiaoInvalida):
        leitor.ler_regiao(caminho, roi)
