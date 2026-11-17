"""Testes unitários para linceu.regiao: campo equivalente e cálculo de ROI."""

import math

import pytest

from linceu.microscopia import Microscopio, Objetiva, Ocular
from linceu.regiao.campo_equivalente import calcular_campo_equivalente
from linceu.regiao.roi import calcular_roi
from linceu.scanner.calibracao import ParametrosCalibracao
from linceu.utilitarios.excecoes import ErroRegiaoInvalida


@pytest.fixture
def cor_padrao():
    escopo = Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0))
    return escopo.campo_optico_referencia


def test_campo_equivalente_diametro_px_isotropico(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=1000, centro_y_px=1000)

    diametro_um_esperado = (22.0 / 100.0) * 1000.0  # mm -> um
    diametro_px_esperado = diametro_um_esperado / 0.25
    assert campo.diametro_px == pytest.approx(diametro_px_esperado)
    assert campo.centro_px == (1000, 1000)


def test_campo_equivalente_area_px_corresponde_a_pi_r_quadrado(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=0, centro_y_px=0)

    esperado = math.pi * campo.raio_px**2
    assert campo.area_px.valor == pytest.approx(esperado)


def test_campo_equivalente_area_px_pixels_nao_quadrados(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.5)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=0, centro_y_px=0)

    raio_x = campo.diametro_px / 2.0
    raio_y = calibracao.pixels_y(campo.diametro) / 2.0
    esperado = math.pi * raio_x * raio_y
    assert campo.area_px.valor == pytest.approx(esperado)
    # com micra_y maior, o campo cobre menos pixels em Y do que em X
    assert raio_y < raio_x


def test_campo_equivalente_preserva_area_fisica(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=500, centro_y_px=500)
    assert campo.area.valor == pytest.approx(cor_padrao.area.valor)
    assert campo.diametro.valor == pytest.approx(cor_padrao.diametro.valor)


def test_calcular_roi_produz_caixa_quadrada_centrada(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=1000, centro_y_px=1000)
    roi = calcular_roi(campo)

    assert roi.largura_px == roi.altura_px
    raio_px = campo.diametro_px / 2.0
    assert roi.x_px == pytest.approx(1000 - raio_px, abs=1)
    assert roi.y_px == pytest.approx(1000 - raio_px, abs=1)
    assert roi.nivel == 0


def test_calcular_roi_registra_nivel_solicitado(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.5, micra_y=0.5, nivel=2)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=500, centro_y_px=500)
    roi = calcular_roi(campo)
    assert roi.nivel == 2


def test_calcular_roi_fora_da_borda_levanta_erro(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    # centro muito próximo da origem faz a caixa ultrapassar a borda superior/esquerda
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=1, centro_y_px=1)
    with pytest.raises(ErroRegiaoInvalida):
        calcular_roi(campo)


def test_campo_equivalente_e_roi_consistentes_entre_si(cor_padrao):
    calibracao = ParametrosCalibracao(micra_x=0.25, micra_y=0.25)
    campo = calcular_campo_equivalente(cor_padrao, calibracao, centro_x_px=2000, centro_y_px=2000)
    roi = calcular_roi(campo)

    # o centro do campo deve estar dentro da caixa delimitadora da ROI
    x0, y0, x1, y1 = roi.caixa_pixels
    assert x0 <= campo.centro_x_px <= x1
    assert y0 <= campo.centro_y_px <= y1
