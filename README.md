# linceu

[![CI](https://github.com/secundinofelipe/linceu/actions/workflows/ci.yml/badge.svg)](https://github.com/secundinofelipe/linceu/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**English** · [Português](#português)

## English

`linceu` is a small Python infrastructure library for **Whole Slide Imaging (WSI)**. It does three things:

1. **Reads TIFF / BigTIFF slides** (`.tif`, `.tiff`, `.btf`): physical resolution (µm/pixel), dimensions and the resolution pyramid.
2. **Calibrates**: converts between scanner pixels and physical units, and between a microscope's optical field (`D = FN / M`) and the pixel space of a digitised slide.
3. **Extracts regions of interest**: computes the *equivalent field* of a microscope on the scanner image ("what would I see through the eyepiece, centred here?") and reads the matching ROI **tile-by-tile**, so memory depends on the ROI size, not on the slide size.

The library is deliberately **analysis-agnostic**: no classification, counting, segmentation or AI. Concrete protocols are built *on top* of it.

```bash
pip install -e .          # from a clone of this repository
```

Requires Python ≥ 3.11. Dependencies: `numpy`, `tifffile`, `zarr` (tile-wise reading) and `imagecodecs` (JPEG / JPEG 2000 / LZW tiles, common in WSI).

```python
from linceu import (Ocular, Objetiva, Microscopio, LeitorTiff, calibrar,
                    calcular_campo_equivalente, calcular_roi)

cor = Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0)).campo_optico_referencia
leitor = LeitorTiff()
calibracao = calibrar(leitor.ler_metadados("slide.btf"))
campo = calcular_campo_equivalente(cor, calibracao, centro_x_px=4000, centro_y_px=3000)
roi = calcular_roi(campo)                       # square bounding box of the circular field
pixels = leitor.ler_regiao("slide.btf", roi)    # numpy array (height, width, channels)
```

Notes: the ROI is the **square** around the circular field (no circular mask is applied); only TIFF/BigTIFF is supported (convert SVS/NDPI/etc. beforehand); the API and docstrings are in Portuguese.

**Citation:** see [`CITATION.cff`](CITATION.cff). **Changes:** see [`CHANGELOG.md`](CHANGELOG.md). **Contributing:** see [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Português

`linceu` é uma biblioteca de infraestrutura para **Whole Slide Imaging (WSI)** em Python, com três responsabilidades:

1. **Leitura de imagens** — arquivos TIFF e BigTIFF (`.tif`, `.tiff`, `.btf`), incluindo resolução física e pirâmide de níveis.
2. **Calibração** — conversão entre pixels do scanner e medidas físicas, e entre o campo óptico de um microscópio e o espaço de pixels de uma imagem digitalizada.
3. **Manipulação geométrica de regiões** — cálculo do campo equivalente do microscópio na imagem do scanner e extração da Região de Interesse (ROI) correspondente, **lendo apenas os tiles necessários** (a memória depende do tamanho da ROI, não da lâmina).

A biblioteca é **agnóstica a qualquer protocolo de análise**: não classifica, não conta objetos, não segmenta e não implementa regra de diagnóstico. Protocolos concretos (ex.: um esquema de graduação clínica, uma métrica de densidade) devem ser construídos **por cima** dela, em código externo.

## Instalação

```bash
git clone https://github.com/secundinofelipe/linceu.git
cd linceu
pip install -e .
```

Requer Python ≥ 3.11. Dependências: `numpy`, `tifffile`, `zarr` (leitura por tiles) e `imagecodecs` (tiles JPEG / JPEG 2000 / LZW, comuns em WSI).

## Arquitetura

```
linceu/
├── geometria/    Primitivas dimensionalmente seguras: Comprimento, Area, Circulo, RazaoArea
├── microscopia/  Configuração óptica: Ocular, Objetiva, Microscopio, CampoOpticoReferencia (COR)
├── scanner/      Metadados de aquisição, pirâmide de níveis, calibração, ImagemDigital
├── es/           Leitura de arquivos: LeitorTiff (TIFF/BigTIFF)
├── regiao/       Campo equivalente do microscópio na imagem + cálculo de ROI
└── utilitarios/  Exceções e validadores compartilhados
```

Cada subpacote depende apenas dos "abaixo" dele nesta lista, sem ciclos de importação (`utilitarios` é a base de todos).

| Subpacote | Responsabilidade única |
|---|---|
| `geometria` | Grandezas físicas rotuladas por unidade (mm, µm, px) e geometria circular, sem noção de microscópio ou scanner. |
| `microscopia` | Representa ocular, objetiva e microscópio; deriva o Campo Óptico de Referência (`D = FN / M`). |
| `scanner` | Metadados de aquisição (resolução, dimensões, pirâmide) e regiões de imagem calibradas e posicionadas. |
| `es` | Único ponto de contato com arquivos em disco: lê metadados e extrai pixels de TIFF/BigTIFF. |
| `regiao` | Projeta o campo óptico do microscópio sobre a imagem do scanner e calcula a ROI correspondente. |

## Uso básico

```python
from linceu import (
    Ocular, Objetiva, Microscopio,
    LeitorTiff, calibrar,
    calcular_campo_equivalente, calcular_roi,
)

# 1. Configuração óptica do microscópio -> Campo Óptico de Referência (COR)
escopo = Microscopio(Ocular(numero_campo=22.0), Objetiva(ampliacao=100.0))
cor = escopo.campo_optico_referencia

# 2. Metadados da lâmina (resolução, dimensões, pirâmide) e calibração (nível 0)
leitor = LeitorTiff()
metadados = leitor.ler_metadados("lamina.btf")
calibracao = calibrar(metadados)

# 3. Campo equivalente do microscópio, centrado em (x, y) pixels do scanner
campo = calcular_campo_equivalente(cor, calibracao, centro_x_px=4000, centro_y_px=3000)
print(campo.diametro_px, campo.area_px, campo.area)

# 4. ROI (caixa quadrada que circunscreve o campo) e extração dos pixels
roi = calcular_roi(campo)
pixels = leitor.ler_regiao("lamina.btf", roi)  # numpy.ndarray (altura, largura, canais)
```

Um exemplo completo e executável (com lâmina sintética) está em [`exemplos/exemplo_uso.py`](exemplos/exemplo_uso.py).

### Trabalhando em outros níveis da pirâmide

O nível de pirâmide viaja **dentro da calibração**, então não dá para ler coordenadas de um nível em outro por engano:

```python
nivel = metadados.nivel(2)                       # NivelPiramide (downsample 4x, por exemplo)
calibracao_n2 = calibrar(metadados).em_nivel(nivel)   # micra/pixel do nível 2; calibracao_n2.nivel == 2
campo = calcular_campo_equivalente(cor, calibracao_n2, centro_x_px=1000, centro_y_px=750)
roi = calcular_roi(campo)                        # roi.nivel == 2
pixels = leitor.ler_regiao("lamina.btf", roi)    # lê o nível 2
```

## Conversões disponíveis

* `Comprimento.converter_para(...)` — mm ⇄ µm ⇄ px (px exige `micra_por_pixel`).
* `ParametrosCalibracao.pixels_x/pixels_y` e `.comprimento_pixel_x/comprimento_pixel_y` — µm ⇄ pixels.
* `CampoEquivalente.diametro_px` / `.area_px` — campo óptico do microscópio ⇄ pixels da imagem do scanner.
* `linceu.scanner.piramide.converter_coordenada/converter_dimensao/converter_caixa_pixels` — coordenadas entre níveis da pirâmide.

## Detalhes importantes

* **ROI quadrada, sem máscara circular.** `calcular_roi` devolve o quadrado que circunscreve o campo circular, arredondado para fora (o círculo sempre cabe). Os pixels dos cantos, fora do círculo, fazem parte do array extraído; aplique uma máscara se precisar.
* **Resolução física.** `ler_metadados` usa `MPP = ...` em `ImageDescription` (convenção de vários scanners) e, na falta dela, as tags TIFF `XResolution`/`YResolution`/`ResolutionUnit` (polegada ou centímetro). Sem nenhuma das duas, levanta `ErroCalibracao`; nesse caso, informe a calibração manualmente com `ParametrosCalibracao(micra_x=..., micra_y=...)`.
* **Formatos.** Apenas TIFF/BigTIFF com eixos `YX`/`YXS` (tiles ou strips; piramidal ou não). Para SVS, NDPI, DICOM etc., converta antes para (Big)TIFF piramidal ou adicione um leitor em `linceu.es` seguindo o contrato de `LeitorTiff`. TIFFs com planos separados (`CYX`/`SYX`) levantam `ErroFormatoNaoSuportado`.
* **Memória.** `LeitorTiff.ler_regiao` lê só os tiles/strips que intersectam a ROI; é seguro para lâminas de vários GB.

## Testes

```bash
pip install -e ".[dev]"
pytest                  # testes + doctests
ruff check . && mypy linceu
python verificar.py     # verificação autônoma, sem pytest
```

## O que esta biblioteca não faz

De propósito, `linceu` **não** inclui:

* Qualquer protocolo de análise (classificação, graduação, contagem).
* Segmentação, detecção ou qualquer componente de IA.
* Interface gráfica ou pipelines de processamento.
* Formatos além de TIFF/BigTIFF (veja *Formatos* acima).

## Citação

Se usar o `linceu` em um trabalho acadêmico, cite-o conforme [`CITATION.cff`](CITATION.cff) (o GitHub exibe o botão *Cite this repository*).

## Licença

MIT — veja [`LICENSE`](LICENSE).
