"""
linceu.utilitarios.validacao
==============================

Validadores pequenos e componíveis, usados em toda a biblioteca para
impor invariantes de domínio no momento da construção. Todo objeto de
valor imutável em ``linceu`` chama este módulo a partir de seu
``__post_init__``, de modo que um objeto inválido seja
*irrepresentável*, e não apenas "não verificado".

Nota de design
---------------
Estas funções levantam :class:`~linceu.utilitarios.excecoes.ErroGeometriaInvalida`
por padrão, mas aceitam um parâmetro ``excecao`` para que chamadores de
outras camadas (ex.: calibração) possam substituir por um tipo de
exceção mais específico, reaproveitando a mesma lógica de validação.
"""

from __future__ import annotations

import math

from linceu.utilitarios.excecoes import ErroGeometriaInvalida, ErroLinceu


def exigir_positivo(
    valor: float,
    nome: str,
    excecao: type[ErroLinceu] = ErroGeometriaInvalida,
) -> float:
    """Valida que ``valor`` é estritamente maior que zero.

    Parâmetros
    ----------
    valor:
        O valor numérico a validar.
    nome:
        Nome legível da grandeza, usado na mensagem de erro.
    excecao:
        Classe de exceção a levantar em caso de falha.

    Retorna
    -------
    float
        O valor validado, inalterado (permite uso em linha).

    Levanta
    -------
    ErroLinceu
        Se ``valor`` não for finito (NaN ou infinito) ou não for
        estritamente positivo.
    """
    if not math.isfinite(valor):
        raise excecao(f"{nome} deve ser um número finito, recebido {valor!r}.")
    if valor <= 0:
        raise excecao(f"{nome} deve ser estritamente positivo, recebido {valor!r}.")
    return valor


def exigir_nao_negativo(
    valor: float,
    nome: str,
    excecao: type[ErroLinceu] = ErroGeometriaInvalida,
) -> float:
    """Valida que ``valor`` é finito e maior ou igual a zero."""
    if not math.isfinite(valor):
        raise excecao(f"{nome} deve ser um número finito, recebido {valor!r}.")
    if valor < 0:
        raise excecao(f"{nome} deve ser não negativo, recebido {valor!r}.")
    return valor


def exigir_inteiro_positivo(
    valor: int,
    nome: str,
    excecao: type[ErroLinceu] = ErroGeometriaInvalida,
) -> int:
    """Valida que ``valor`` é um número inteiro estritamente positivo.

    ``bool`` é explicitamente rejeitado apesar de ser subclasse de
    ``int`` em Python: ``True``/``False`` nunca são uma contagem ou
    dimensão válida nesta biblioteca.
    """
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise excecao(f"{nome} deve ser um inteiro, recebido {type(valor).__name__}.")
    if valor <= 0:
        raise excecao(f"{nome} deve ser estritamente positivo, recebido {valor!r}.")
    return valor


def exigir_inteiro_nao_negativo(
    valor: int,
    nome: str,
    excecao: type[ErroLinceu] = ErroGeometriaInvalida,
) -> int:
    """Valida que ``valor`` é um número inteiro maior ou igual a zero.

    Espelha :func:`exigir_inteiro_positivo`, mas permite zero. ``bool``
    também é explicitamente rejeitado pelo mesmo motivo.
    """
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise excecao(f"{nome} deve ser um inteiro, recebido {type(valor).__name__}.")
    if valor < 0:
        raise excecao(f"{nome} deve ser não negativo, recebido {valor!r}.")
    return valor


def exigir_string_nao_vazia(
    valor: str,
    nome: str,
    excecao: type[ErroLinceu] = ErroGeometriaInvalida,
) -> str:
    """Valida que ``valor`` é uma string não vazia e não composta apenas
    por espaços em branco."""
    if not isinstance(valor, str) or not valor.strip():
        raise excecao(f"{nome} deve ser uma string não vazia, recebido {valor!r}.")
    return valor
