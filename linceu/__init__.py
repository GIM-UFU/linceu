"""
linceu — Infraestrutura para Whole Slide Imaging (WSI)
==========================================================

``linceu`` é uma biblioteca de infraestrutura para trabalhar com
Imagens de Lâmina Inteira (Whole Slide Imaging): leitura de arquivos
TIFF/BigTIFF, representação de configurações de scanner e de
microscópio, e cálculo/extração de regiões de interesse a partir do
campo óptico de um microscópio projetado sobre a imagem digitalizada.

A biblioteca é deliberadamente agnóstica a qualquer protocolo de
análise: ela não classifica, não conta objetos e não implementa regras
de negócio de diagnóstico. Protocolos concretos (ex.: um esquema de
graduação, uma métrica de densidade normalizada) são construídos
*sobre* esta biblioteca, em código externo a ela.

O pacote está organizado em cinco subpacotes em camadas:

* :mod:`~linceu.geometria` — primitivas geométricas dimensionalmente
  seguras (comprimento, área, círculo), sem qualquer noção de
  microscopia ou aquisição de imagem.
* :mod:`~linceu.microscopia` — configuração óptica do microscópio
  (ocular, objetiva) e o Campo Óptico de Referência (COR) que ela
  produz.
* :mod:`~linceu.scanner` — configuração de aquisição do scanner
  (resolução, dimensões, pirâmide de níveis) e representação de
  regiões de imagem calibradas.
* :mod:`~linceu.es` — leitura de arquivos TIFF/BigTIFF.
* :mod:`~linceu.regiao` — cálculo do campo equivalente do microscópio
  na imagem do scanner e extração da Região de Interesse (ROI)
  correspondente.

Início rápido
--------------
Configuração óptica e Campo Óptico de Referência (COR):

>>> from linceu import Ocular, Objetiva, Microscopio
>>> escopo = Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0))
>>> cor = escopo.campo_optico_referencia
>>> cor.diametro
Comprimento(0.22 mm)

Leitura de uma lâmina real, campo equivalente e ROI (precisa de um
arquivo, por isso estas linhas não são executadas nos doctests):

>>> from linceu import LeitorTiff, calibrar, calcular_campo_equivalente, calcular_roi
>>> leitor = LeitorTiff()
>>> metadados = leitor.ler_metadados("lamina.btf")  # doctest: +SKIP
>>> calibracao = calibrar(metadados)  # doctest: +SKIP
>>> campo = calcular_campo_equivalente(cor, calibracao, 4000, 3000)  # doctest: +SKIP
>>> roi = calcular_roi(campo)  # doctest: +SKIP
>>> pixels = leitor.ler_regiao("lamina.btf", roi)  # doctest: +SKIP
"""

from __future__ import annotations

from linceu.es import LeitorTiff
from linceu.geometria import (
    Area,
    Circulo,
    Comprimento,
    RazaoArea,
    TemArea,
    UnidadeArea,
    UnidadeComprimento,
)
from linceu.microscopia import CampoOpticoReferencia, Microscopio, Objetiva, Ocular
from linceu.regiao import CampoEquivalente, calcular_campo_equivalente, calcular_roi
from linceu.scanner import (
    ImagemDigital,
    MetadadosScanner,
    NivelPiramide,
    ParametrosCalibracao,
    calibrar,
    converter_caixa_pixels,
    converter_coordenada,
    converter_dimensao,
)
from linceu.utilitarios import (
    ErroCalibracao,
    ErroFormatoNaoSuportado,
    ErroGeometriaInvalida,
    ErroIncompatibilidadeUnidade,
    ErroLinceu,
    ErroRegiaoInvalida,
)

__version__ = "2.1.0"

__all__ = [
    "__version__",
    # geometria
    "Comprimento",
    "UnidadeComprimento",
    "Area",
    "UnidadeArea",
    "Circulo",
    "RazaoArea",
    "TemArea",
    # microscopia
    "Ocular",
    "Objetiva",
    "Microscopio",
    "CampoOpticoReferencia",
    # scanner
    "MetadadosScanner",
    "NivelPiramide",
    "ParametrosCalibracao",
    "calibrar",
    "ImagemDigital",
    "converter_coordenada",
    "converter_dimensao",
    "converter_caixa_pixels",
    # es
    "LeitorTiff",
    # regiao
    "CampoEquivalente",
    "calcular_campo_equivalente",
    "calcular_roi",
    # erros
    "ErroLinceu",
    "ErroIncompatibilidadeUnidade",
    "ErroGeometriaInvalida",
    "ErroCalibracao",
    "ErroFormatoNaoSuportado",
    "ErroRegiaoInvalida",
]
