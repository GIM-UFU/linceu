"""
linceu.regiao
================

Conecta a configuração óptica do microscópio
(:mod:`linceu.microscopia`) à imagem digitalizada do scanner
(:mod:`linceu.scanner`): calcula o **campo equivalente** — a projeção
do campo óptico do microscópio sobre o espaço de pixels de uma imagem
de scanner, centrada em um ponto arbitrário
(:mod:`linceu.regiao.campo_equivalente`) — e deriva dele a Região de
Interesse (ROI) retangular correspondente, pronta para extração de
pixels via :mod:`linceu.es` (:mod:`linceu.regiao.roi`).
"""

from linceu.regiao.campo_equivalente import CampoEquivalente, calcular_campo_equivalente
from linceu.regiao.roi import calcular_roi

__all__ = ["CampoEquivalente", "calcular_campo_equivalente", "calcular_roi"]
