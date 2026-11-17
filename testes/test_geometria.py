"""Testes unitários para linceu.geometria: unidades, círculo, razão de área."""

import math

import pytest

from linceu.geometria.area import RazaoArea
from linceu.geometria.circulo import Circulo, area_para_diametro, diametro_para_area
from linceu.geometria.unidades import Area, Comprimento, UnidadeArea, UnidadeComprimento
from linceu.utilitarios.excecoes import ErroGeometriaInvalida, ErroIncompatibilidadeUnidade


def test_conversao_comprimento_mm_para_um():
    comprimento = Comprimento(1.0, UnidadeComprimento.MILIMETRO)
    convertido = comprimento.converter_para(UnidadeComprimento.MICROMETRO)
    assert convertido.valor == pytest.approx(1000.0)
    assert convertido.unidade is UnidadeComprimento.MICROMETRO


def test_comprimento_negativo_rejeitado():
    with pytest.raises(ErroGeometriaInvalida):
        Comprimento(-1.0, UnidadeComprimento.MILIMETRO)


def test_soma_comprimento_mesma_unidade():
    a = Comprimento(1.0, UnidadeComprimento.MILIMETRO)
    b = Comprimento(2.0, UnidadeComprimento.MILIMETRO)
    assert (a + b).valor == pytest.approx(3.0)


def test_soma_comprimento_unidades_diferentes_levanta_erro():
    a = Comprimento(1.0, UnidadeComprimento.MILIMETRO)
    b = Comprimento(2.0, UnidadeComprimento.MICROMETRO)
    with pytest.raises(ErroIncompatibilidadeUnidade):
        _ = a + b


def test_comprimento_pixel_exige_calibracao():
    px = Comprimento(100.0, UnidadeComprimento.PIXEL)
    with pytest.raises(ErroIncompatibilidadeUnidade):
        px.converter_para(UnidadeComprimento.MICROMETRO)
    convertido = px.converter_para(UnidadeComprimento.MICROMETRO, micra_por_pixel=0.25)
    assert convertido.valor == pytest.approx(25.0)


def test_diametro_para_area_corresponde_a_pi_r_quadrado():
    d = Comprimento(22.0, UnidadeComprimento.MILIMETRO)
    area = diametro_para_area(d)
    esperado = math.pi * (11.0**2)
    assert area.valor == pytest.approx(esperado)
    assert area.unidade is UnidadeArea.MILIMETRO_QUADRADO


def test_area_para_diametro_e_inversa_de_diametro_para_area():
    d = Comprimento(18.0, UnidadeComprimento.MILIMETRO)
    a = diametro_para_area(d)
    d2 = area_para_diametro(a)
    assert d2.valor == pytest.approx(d.valor)


def test_propriedade_area_circulo():
    c = Circulo(diametro=Comprimento(2.0, UnidadeComprimento.CENTIMETRO))
    assert c.area.valor == pytest.approx(math.pi)
    assert c.raio.valor == pytest.approx(1.0)


def test_razao_area_adimensional():
    a1 = Area(100.0, UnidadeArea.MICROMETRO_QUADRADO)
    a2 = Area(25.0, UnidadeArea.MICROMETRO_QUADRADO)
    razao = RazaoArea.de(a1, a2)
    assert razao.valor == pytest.approx(4.0)
    assert float(razao) == pytest.approx(4.0)


def test_razao_area_incompatibilidade_unidade_levanta_erro():
    a1 = Area(100.0, UnidadeArea.MICROMETRO_QUADRADO)
    a2 = Area(1.0, UnidadeArea.MILIMETRO_QUADRADO)
    with pytest.raises(ErroIncompatibilidadeUnidade):
        RazaoArea.de(a1, a2)


def test_conversao_area_ida_e_volta():
    a = Area(1.0, UnidadeArea.MILIMETRO_QUADRADO)
    convertida = a.converter_para(UnidadeArea.MICROMETRO_QUADRADO)
    assert convertida.valor == pytest.approx(1_000_000.0)
    de_volta = convertida.converter_para(UnidadeArea.MILIMETRO_QUADRADO)
    assert de_volta.valor == pytest.approx(1.0)
