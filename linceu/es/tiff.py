"""
linceu.es.tiff
=================

Leitor concreto de imagens de lâmina inteira (WSI) em formato TIFF e
BigTIFF (``.tif``, ``.tiff``, ``.btf``), baseado na biblioteca
``tifffile``. É o único adaptador de E/S da biblioteca: lê metadados
(resolução física, dimensões, pirâmide de níveis) e extrai pixels de
uma região arbitrária de um nível específico da pirâmide.

BigTIFF é apenas uma variante do formato TIFF com offsets de 64 bits,
usada para arquivos maiores que 4 GiB; ``tifffile`` lida com ambas as
variantes de forma transparente, sem exigir nenhuma distinção no
código cliente.

A extração de regiões é feita **por tiles/strips** (via
``tifffile`` + ``zarr``): apenas os blocos que intersectam a região
pedida são decodificados, de modo que o uso de memória depende do
tamanho da região, e não do tamanho da lâmina. Para decodificar tiles
comprimidos em JPEG/JPEG 2000/LZW etc. (comuns em WSI), é necessário o
pacote ``imagecodecs``, instalado como dependência da biblioteca.
"""

from __future__ import annotations

import os
import re

import numpy as np
import tifffile
import zarr

from linceu.scanner.imagem import ImagemDigital
from linceu.scanner.metadados import MetadadosScanner, NivelPiramide
from linceu.utilitarios.excecoes import ErroCalibracao, ErroFormatoNaoSuportado, ErroRegiaoInvalida

#: Extensões de arquivo reconhecidas por este leitor.
EXTENSOES_SUPORTADAS = frozenset({".tif", ".tiff", ".btf"})

# Fator de conversão de cada unidade de resolução TIFF para micrômetros.
# Códigos da tag ResolutionUnit: 1 = nenhuma, 2 = polegada, 3 = centímetro.
_UNIDADE_RESOLUCAO_PARA_MICROMETROS = {
    2: 25_400.0,  # 1 polegada = 25400 µm
    3: 10_000.0,  # 1 centímetro = 10000 µm
}

# Reconhece "MPP = 0.2500" ou "MPP=0.25", convenção usada por diversos
# scanners (ex.: Aperio) na tag ImageDescription do TIFF.
_PADRAO_MPP_DESCRICAO = re.compile(r"MPP\s*=\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)


class LeitorTiff:
    """Lê metadados e regiões de pixel de arquivos TIFF/BigTIFF WSI.

    Um :class:`LeitorTiff` não mantém nenhum arquivo aberto entre
    chamadas: cada método abre, lê o que precisa, e fecha o arquivo.
    Isso mantém a classe sem estado e segura para uso concorrente, ao
    custo de reabrir o arquivo a cada chamada — uma troca deliberada
    para manter a implementação simples.
    """

    def suporta(self, caminho: str) -> bool:
        """Retorna ``True`` se ``caminho`` tiver uma extensão TIFF/BigTIFF
        reconhecida."""
        _, ext = os.path.splitext(caminho)
        return ext.lower() in EXTENSOES_SUPORTADAS

    def ler_metadados(self, caminho: str) -> MetadadosScanner:
        """Lê os :class:`~linceu.scanner.metadados.MetadadosScanner` de
        um arquivo TIFF/BigTIFF, incluindo sua pirâmide de níveis.

        A resolução física (micra por pixel) é obtida, em ordem de
        preferência: (1) de uma marcação ``MPP = ...`` na tag
        ``ImageDescription`` do nível 0 (convenção comum entre
        scanners de lâmina), ou (2) das tags TIFF padrão
        ``XResolution``/``YResolution``/``ResolutionUnit``.

        Levanta
        -------
        ErroFormatoNaoSuportado
            Se ``caminho`` não tiver uma extensão TIFF/BigTIFF reconhecida
            ou não puder ser aberto como TIFF.
        ErroCalibracao
            Se nenhuma informação de resolução física puder ser
            determinada a partir do arquivo.
        """
        if not self.suporta(caminho):
            raise ErroFormatoNaoSuportado(
                f"LeitorTiff só suporta arquivos {sorted(EXTENSOES_SUPORTADAS)}, recebido {caminho!r}."
            )

        try:
            with tifffile.TiffFile(caminho) as arquivo:
                serie = arquivo.series[0]
                niveis_origem = serie.levels

                pagina_base = niveis_origem[0].keyframe
                largura_px = int(pagina_base.imagewidth)
                altura_px = int(pagina_base.imagelength)

                micra_x, micra_y = self._resolucao_fisica(pagina_base)

                niveis: list[NivelPiramide] = []
                for indice, nivel in enumerate(niveis_origem):
                    pagina = nivel.keyframe
                    largura_nivel = int(pagina.imagewidth)
                    fator_downsample = largura_px / largura_nivel
                    niveis.append(
                        NivelPiramide(
                            indice=indice,
                            largura_px=largura_nivel,
                            altura_px=int(pagina.imagelength),
                            fator_downsample=fator_downsample,
                        )
                    )

                fabricante = self._detectar_fabricante(pagina_base)

                return MetadadosScanner(
                    micra_x=micra_x,
                    micra_y=micra_y,
                    largura_px=largura_px,
                    altura_px=altura_px,
                    niveis=tuple(niveis),
                    fabricante=fabricante,
                )
        except tifffile.TiffFileError as exc:
            raise ErroFormatoNaoSuportado(f"Falha ao abrir {caminho!r} como TIFF: {exc}") from exc

    def ler_regiao(self, caminho: str, imagem: ImagemDigital) -> np.ndarray:
        """Extrai os pixels correspondentes a ``imagem`` do arquivo em
        ``caminho``, como um array NumPy.

        ``imagem.nivel`` seleciona o nível de pirâmide de onde ler, e
        ``imagem.caixa_pixels`` (derivada de ``x_px``, ``y_px``,
        ``largura_px``, ``altura_px``) delimita a região dentro desse
        nível. O array retornado tem forma ``(altura_px, largura_px, ...)``
        e é sempre uma cópia independente.

        Apenas os tiles/strips que intersectam a região são
        decodificados; o nível inteiro **nunca** é carregado em memória,
        então esta chamada é segura para lâminas de vários GB.

        Levanta
        -------
        ErroRegiaoInvalida
            Se a região solicitada estiver total ou parcialmente fora
            dos limites do nível de pirâmide indicado, ou se o nível não
            existir.
        ErroFormatoNaoSuportado
            Se o arquivo não for TIFF/BigTIFF legível, ou se seus eixos
            não começarem por ``YX`` (ex.: TIFF com planos separados
            ``CYX``/``SYX``, ainda não suportado).
        """
        try:
            with tifffile.TiffFile(caminho) as arquivo:
                serie = arquivo.series[0]
                niveis_origem = serie.levels
                if imagem.nivel >= len(niveis_origem):
                    raise ErroRegiaoInvalida(
                        f"Nível de pirâmide {imagem.nivel} inexistente neste arquivo "
                        f"(níveis disponíveis: 0..{len(niveis_origem) - 1})."
                    )

                nivel_serie = niveis_origem[imagem.nivel]
                if not nivel_serie.axes.startswith("YX"):
                    raise ErroFormatoNaoSuportado(
                        f"Eixos {nivel_serie.axes!r} não suportados: LeitorTiff espera eixos "
                        f"começando por 'YX' (ex.: 'YX' ou 'YXS')."
                    )
                altura_disponivel = int(nivel_serie.shape[0])
                largura_disponivel = int(nivel_serie.shape[1])

                x0, y0, x1, y1 = imagem.caixa_pixels
                if x0 < 0 or y0 < 0 or x1 > largura_disponivel or y1 > altura_disponivel:
                    raise ErroRegiaoInvalida(
                        f"Região {(x0, y0, x1, y1)} excede os limites do nível "
                        f"{imagem.nivel} ({largura_disponivel}x{altura_disponivel}px)."
                    )

                armazem = serie.aszarr(level=imagem.nivel)
                try:
                    dados = zarr.open_array(armazem, mode="r")
                    return np.array(dados[y0:y1, x0:x1, ...])
                finally:
                    armazem.close()
        except tifffile.TiffFileError as exc:
            raise ErroFormatoNaoSuportado(f"Falha ao abrir {caminho!r} como TIFF: {exc}") from exc

    @staticmethod
    def _resolucao_fisica(pagina: tifffile.TiffPage) -> tuple[float, float]:
        """Determina (micra_x, micra_y) a partir de uma página TIFF."""
        descricao = pagina.tags.get("ImageDescription")
        if descricao is not None:
            casamento = _PADRAO_MPP_DESCRICAO.search(str(descricao.value))
            if casamento:
                mpp = float(casamento.group(1))
                return mpp, mpp

        resolucao = pagina.resolution if pagina.resolution else None
        unidade = pagina.resolutionunit

        if resolucao and unidade in _UNIDADE_RESOLUCAO_PARA_MICROMETROS:
            um_por_unidade = _UNIDADE_RESOLUCAO_PARA_MICROMETROS[unidade]
            pixels_por_x, pixels_por_y = resolucao
            if pixels_por_x > 0 and pixels_por_y > 0:
                return um_por_unidade / pixels_por_x, um_por_unidade / pixels_por_y

        raise ErroCalibracao(
            "Não foi possível determinar a resolução física (micra por pixel) "
            "a partir dos metadados do TIFF; forneça a calibração explicitamente "
            "via linceu.scanner.calibracao.ParametrosCalibracao."
        )

    @staticmethod
    def _detectar_fabricante(pagina: tifffile.TiffPage) -> str:
        descricao = pagina.tags.get("ImageDescription")
        texto = str(descricao.value) if descricao is not None else ""
        marcadores = ("Aperio", "Hamamatsu", "Leica", "3DHistech", "Philips", "Zeiss")
        for marcador in marcadores:
            if marcador.lower() in texto.lower():
                return marcador
        fabricante_tag = pagina.tags.get("Make")
        if fabricante_tag is not None and str(fabricante_tag.value).strip():
            return str(fabricante_tag.value).strip()
        return "desconhecido"
