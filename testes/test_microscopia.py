"""Testes unitários para linceu.microscopia: Ocular, Objetiva, Microscopio, COR.

Verifica a Definição 1 da especificação:
    D_COR = FN / M
    A_COR = pi * (D_COR / 2)^2
"""

import math

import pytest

from linceu.geometria.unidades import UnidadeComprimento
from linceu.microscopia import CampoOpticoReferencia, Microscopio, Objetiva, Ocular
from linceu.utilitarios.excecoes import ErroGeometriaInvalida


def test_formula_diametro_cor():
    ocular = Ocular(numero_campo=22.0)
    objetiva = Objetiva(ampliacao=100.0)
    cor = CampoOpticoReferencia.a_partir_de_configuracao_microscopio(ocular, objetiva)

    diametro_esperado_mm = 22.0 / 100.0
    assert cor.diametro.unidade is UnidadeComprimento.MILIMETRO
    assert cor.diametro.valor == pytest.approx(diametro_esperado_mm)


def test_formula_area_cor():
    ocular = Ocular(numero_campo=20.0)
    objetiva = Objetiva(ampliacao=40.0)
    cor = CampoOpticoReferencia.a_partir_de_configuracao_microscopio(ocular, objetiva)

    d = 20.0 / 40.0
    area_esperada = math.pi * (d / 2.0) ** 2
    assert cor.area.valor == pytest.approx(area_esperada)


def test_agregado_microscopio_corresponde_a_construcao_direta():
    ocular = Ocular(numero_campo=22.0)
    objetiva = Objetiva(ampliacao=100.0)
    escopo = Microscopio(ocular, objetiva)

    direto = CampoOpticoReferencia.a_partir_de_configuracao_microscopio(ocular, objetiva)
    assert escopo.campo_optico_referencia.diametro.valor == pytest.approx(direto.diametro.valor)
    assert escopo.campo_optico_referencia.area.valor == pytest.approx(direto.area.valor)


def test_ampliacao_total_microscopio():
    escopo = Microscopio(Ocular(numero_campo=22.0, ampliacao=10.0), Objetiva(ampliacao=100.0))
    assert escopo.ampliacao_total == pytest.approx(1000.0)


def test_ocular_rejeita_numero_campo_nao_positivo():
    with pytest.raises(ErroGeometriaInvalida):
        Ocular(numero_campo=0.0)
    with pytest.raises(ErroGeometriaInvalida):
        Ocular(numero_campo=-5.0)


def test_objetiva_rejeita_ampliacao_nao_positiva():
    with pytest.raises(ErroGeometriaInvalida):
        Objetiva(ampliacao=0.0)


def test_objetiva_rejeita_abertura_numerica_implausivel():
    with pytest.raises(ErroGeometriaInvalida):
        Objetiva(ampliacao=100.0, abertura_numerica=2.0)


def test_cada_configuracao_define_um_cor_unico():
    escopo_a = Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0))
    escopo_b = Microscopio(Ocular(numero_campo=20.0), Objetiva(ampliacao=40.0))
    assert escopo_a.campo_optico_referencia.diametro.valor != pytest.approx(
        escopo_b.campo_optico_referencia.diametro.valor
    )
