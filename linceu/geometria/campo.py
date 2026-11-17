"""
linceu.geometria.campo
=========================

Protocolo estrutural (PEP 544) que descreve qualquer coisa que possua
uma ``area`` física — um "campo de visão". Tanto o campo óptico do
microscópio (:class:`linceu.microscopia.campo_optico.CampoOpticoReferencia`)
quanto uma região de imagem digital escaneada
(:class:`linceu.scanner.imagem.ImagemDigital`) satisfazem este
protocolo, o que é precisamente o que permite à camada de cálculo de
regiões (:mod:`linceu.regiao`) relacionar os dois de forma genérica —
como uma razão ou projeção entre dois objetos ``TemArea`` — sem
depender de nenhum dos dois tipos concretos. Esta é a materialização,
em nível de geometria, do Princípio de Inversão de Dependência.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from linceu.geometria.unidades import Area


@runtime_checkable
class TemArea(Protocol):
    """Interface estrutural para qualquer entidade que exponha uma
    ``area`` física."""

    @property
    def area(self) -> Area:
        """A área física deste campo de visão."""
        ...
