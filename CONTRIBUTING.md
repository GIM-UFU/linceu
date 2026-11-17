# Contribuindo

Obrigado pelo interesse! Antes de abrir um *pull request*:

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .   # estilo
mypy linceu                             # tipagem estrita
pytest                                  # testes + doctests
python verificar.py                     # verificação autônoma
```

Diretrizes:

- A biblioteca é **agnóstica a protocolos de análise** (sem classificação,
  contagem, segmentação ou IA). Esse código deve viver em pacotes externos,
  construídos sobre o `linceu`.
- Respeite a hierarquia de camadas descrita no README (sem ciclos de import).
- Todo comportamento novo precisa de teste; toda API pública, de docstring.
- Novos formatos de imagem entram como leitores em `linceu.es`, seguindo o
  contrato de `LeitorTiff`.
- Nunca inclua lâminas reais ou dados de pacientes em *commits*, *issues* ou
  testes: use imagens sintéticas (veja `testes/` e `exemplos/`).
