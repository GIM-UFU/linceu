"""Testes unitários para linceu.scanner: metadados, pirâmide, calibração e ImagemDigital."""

import pytest

from linceu.geometria.unidades import UnidadeArea
from linceu.scanner.calibracao import ParametrosCalibracao, calibrar
from linceu.scanner.imagem import ImagemDigital
from linceu.scanner.metadados import MetadadosScanner, NivelPiramide
from linceu.scanner.piramide import converter_caixa_pixels, converter_coordenada, converter_dimensao
from linceu.utilitarios.excecoes import ErroCalibracao, ErroRegiaoInvalida


def test_metadados_sem_niveis_explicitos_cria_piramide_de_um_nivel():
    metadados = MetadadosScanner(micra_x=0.25, micra_y=0.25, largura_px=1000, altura_px=800)
    assert len(metadados.niveis) == 1
    assert metadados.niveis[0].indice == 0
    assert not metadados.eh_piramidal


def test_metadados_com_niveis_explicitos():
    niveis = (
        NivelPiramide(indice=0, largura_px=2048, altura_px=2048, fator_downsample=1.0),
        NivelPiramide(indice=1, largura_px=1024, altura_px=1024, fator_downsample=2.0),
    )
    metadados = MetadadosScanner(micra_x=0.25, micra_y=0.25, largura_px=2048, altura_px=2048, niveis=niveis)
    assert metadados.eh_piramidal
    assert metadados.nivel(1).fator_downsample == pytest.approx(2.0)


def test_metadados_nivel_inexistente_levanta_erro():
    metadados = MetadadosScanner(micra_x=0.25, micra_y=0.25, largura_px=100, altura_px=100)
    with pytest.raises(ErroCalibracao):
        metadados.nivel(5)


def test_metadados_rejeita_micra_nao_positivo():
    with pytest.raises(ErroCalibracao):
        MetadadosScanner(micra_x=0.0, micra_y=0.25, largura_px=100, altura_px=100)


def test_metadados_eh_isotropico():
    isotropico = MetadadosScanner(micra_x=0.25, micra_y=0.25, largura_px=10, altura_px=10)
    anisotropico = MetadadosScanner(micra_x=0.25, micra_y=0.30, largura_px=10, altura_px=10)
    assert isotropico.eh_isotropico
    assert not anisotropico.eh_isotropico


def test_calibrar_a_partir_de_metadados():
    metadados = MetadadosScanner(micra_x=0.5, micra_y=0.5, largura_px=100, altura_px=100)
    calibracao = calibrar(metadados)
    assert calibracao.micra_x == pytest.approx(0.5)


def test_calibracao_conversao_px_para_fisico_e_volta():
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    comprimento = calibracao.comprimento_pixel_x(100)
    assert comprimento.valor == pytest.approx(25.0)
    pixels = calibracao.pixels_x(comprimento)
    assert pixels == pytest.approx(100.0)


def test_calibracao_em_nivel_escala_micra_por_downsample():
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    nivel2 = NivelPiramide(indice=2, largura_px=256, altura_px=256, fator_downsample=4.0)
    calibracao_nivel2 = calibracao.em_nivel(nivel2)
    assert calibracao_nivel2.micra_x == pytest.approx(1.0)
    assert calibracao_nivel2.nivel == 2


def test_calibracao_area_pixel():
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    area = calibracao.area_pixel(largura_px=100, altura_px=100)
    assert area.unidade is UnidadeArea.MICROMETRO_QUADRADO
    assert area.valor == pytest.approx(25.0 * 25.0)


def test_imagem_digital_lamina_inteira():
    metadados = MetadadosScanner(micra_x=0.25, micra_y=0.25, largura_px=1000, altura_px=500)
    imagem = ImagemDigital.lamina_inteira(metadados)
    assert imagem.largura_px == 1000
    assert imagem.altura_px == 500
    assert imagem.x_px == 0 and imagem.y_px == 0
    assert imagem.area.valor == pytest.approx(250.0 * 125.0)


def test_imagem_digital_sub_regiao_preserva_calibracao_e_desloca_posicao():
    metadados = MetadadosScanner(micra_x=0.25, micra_y=0.25, largura_px=1000, altura_px=1000)
    inteira = ImagemDigital.lamina_inteira(metadados)
    sub = inteira.sub_regiao(x_px=100, y_px=200, largura_px=50, altura_px=60)
    assert sub.x_px == 100 and sub.y_px == 200
    assert sub.largura_px == 50 and sub.altura_px == 60
    assert sub.calibracao is inteira.calibracao


def test_imagem_digital_caixa_pixels():
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    imagem = ImagemDigital(largura_px=50, altura_px=60, calibracao=calibracao, x_px=10, y_px=20)
    assert imagem.caixa_pixels == (10, 20, 60, 80)


def test_imagem_digital_rejeita_dimensoes_nao_positivas():
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    with pytest.raises(ErroRegiaoInvalida):
        ImagemDigital(largura_px=0, altura_px=10, calibracao=calibracao)


def test_conversao_coordenada_entre_niveis():
    n0 = NivelPiramide(indice=0, largura_px=2048, altura_px=2048, fator_downsample=1.0)
    n2 = NivelPiramide(indice=2, largura_px=512, altura_px=512, fator_downsample=4.0)
    x, y = converter_coordenada(1000, 1000, n0, n2)
    assert x == pytest.approx(250.0)
    assert y == pytest.approx(250.0)

    # a conversão de volta deve ser a inversa
    x0, y0 = converter_coordenada(x, y, n2, n0)
    assert x0 == pytest.approx(1000.0)
    assert y0 == pytest.approx(1000.0)


def test_conversao_dimensao_entre_niveis():
    n0 = NivelPiramide(indice=0, largura_px=2048, altura_px=2048, fator_downsample=1.0)
    n1 = NivelPiramide(indice=1, largura_px=1024, altura_px=1024, fator_downsample=2.0)
    largura, altura = converter_dimensao(200, 100, n0, n1)
    assert largura == pytest.approx(100.0)
    assert altura == pytest.approx(50.0)


def test_conversao_caixa_pixels_entre_niveis():
    n0 = NivelPiramide(indice=0, largura_px=2048, altura_px=2048, fator_downsample=1.0)
    n1 = NivelPiramide(indice=1, largura_px=1024, altura_px=1024, fator_downsample=2.0)
    caixa = converter_caixa_pixels((100, 100, 300, 300), n0, n1)
    assert caixa == pytest.approx((50.0, 50.0, 150.0, 150.0))
