"""Utilitários transversais compartilhados por todas as camadas do ``linceu``.

Este subpacote propositalmente não tem dependências de nenhuma outra
parte do ``linceu`` (fica na base do grafo de dependências), de modo
que pode ser importado com segurança a partir de geometria,
microscopia, scanner, ou E/S, sem criar ciclos de importação.
"""

from linceu.utilitarios.excecoes import (
    ErroCalibracao,
    ErroFormatoNaoSuportado,
    ErroGeometriaInvalida,
    ErroIncompatibilidadeUnidade,
    ErroLinceu,
    ErroRegiaoInvalida,
)

__all__ = [
    "ErroCalibracao",
    "ErroFormatoNaoSuportado",
    "ErroGeometriaInvalida",
    "ErroIncompatibilidadeUnidade",
    "ErroLinceu",
    "ErroRegiaoInvalida",
]
