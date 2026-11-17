"""
linceu.utilitarios.excecoes
=============================

Hierarquia de exceções centralizada do pacote ``linceu``.

Todo erro levantado em qualquer parte da biblioteca — geometria,
microscopia, calibração de scanner, ou leitura de imagem — deriva de
:class:`ErroLinceu`. Isso permite que os consumidores capturem
qualquer falha específica da biblioteca com uma única cláusula
``except ErroLinceu:``, mantendo ainda a possibilidade de tratamento
granular quando necessário.
"""

from __future__ import annotations


class ErroLinceu(Exception):
    """Classe base para todas as exceções levantadas pelo pacote ``linceu``."""


class ErroIncompatibilidadeUnidade(ErroLinceu):
    """Levantado quando uma operação é tentada entre unidades incompatíveis.

    Exemplo
    -------
    Somar um :class:`~linceu.geometria.unidades.Comprimento` expresso em
    micrômetros a uma :class:`~linceu.geometria.unidades.Area` expressa em
    milímetros quadrados é um erro dimensional, não numérico, e por
    isso é reportado por meio desta exceção em vez de ser silenciosamente
    convertido.
    """


class ErroGeometriaInvalida(ErroLinceu):
    """Levantado quando uma grandeza geométrica viola um invariante de domínio.

    Exemplos incluem um diâmetro negativo, uma ampliação não positiva,
    ou um número de campo igual a zero.
    """


class ErroCalibracao(ErroLinceu):
    """Levantado quando os dados de calibração do scanner estão ausentes,
    malformados ou fisicamente implausíveis (ex.: micra-por-pixel não
    positivo)."""


class ErroFormatoNaoSuportado(ErroLinceu):
    """Levantado por um leitor de :mod:`linceu.es` quando solicitado a
    abrir um arquivo que não está em um formato suportado (TIFF/BigTIFF)."""


class ErroRegiaoInvalida(ErroLinceu):
    """Levantado quando uma região de interesse (ROI) solicitada é
    inválida — ex.: fora dos limites da imagem, com dimensões não
    positivas, ou referenciando um nível de pirâmide inexistente."""
