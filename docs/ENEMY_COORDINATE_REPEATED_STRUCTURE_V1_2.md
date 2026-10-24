# Enemy Coordinate Discovery v1.2 — Repeated Structure Validation

## Objetivo
Auditar igualdade de **bytes crus** entre as regiões `A` e `A+0x11800`, comparando duas épocas Freeze ON em `on_stable` e `on_hold`. O teste não depende de float32, endianness nem do ranking anterior. Não altera a RDRAM, a ROM, as capturas ou `GoldenEye.mapping/catalog/symbols.json`.

## Evidência de origem
Operador: entre 716 pares de interpretações candidatas separados por `0x11800`, 572 apresentaram bytes iguais em P1/P2, 75 apenas P1, 44 apenas P2 e 25 em nenhum. A seleção foi condicionada aos filtros de v1/v1.1: isto **não é** uma taxa de espelhamento do bloco completo.

## Método
O analisador lê os mesmos quatro dumps 8 MiB da sessão v1, verificando igualdade `frame == frame_after`, estado ON e metadados de captura. Na janela A padrão `[0x0D5000,0x0D8500)`, compara os bytes em `A+0x11800`. A análise de divergência temporal usa P1 e P2, e estabilidade de cada lado é medida também com os snapshots HOLD.

Controles: offsets relativos `0x10000`, `0x10800`, `0x11000`, `0x11800`, `0x12000`, `0x12800`, `0x13000` com a MESMA janela A. Igualdade com controle não equivale a teste de significância estatística. A comparação por blocos é feita a cada 256 bytes na janela A. A ferramenta sinaliza bytes que mudaram de classe de igualdade ou para os quais somente um dos lados variou; isso não significa que cada byte seja campo diferente.

## Executar
```powershell
git pull --ff-only origin main
python -m unittest tests.test_enemy_freeze_v1_2 -v
$sid="20261024T210536Z_648577"
python -m tools.analyze_enemy_freeze_v1_2 $sid
```

## Saídas (sem sobrescrever)
Todos em `output/csv`, com prefixo `enemy_freeze_v1_2_<sid>`:
- `shift_controls.csv`: igualdade P1/P2 para deslocamento principal e controles.
- `window_equality.csv`: igualdade crua por janelas de 256 bytes em P1.
- `byte_divergences.csv`: bytes cuja relação de igualdade mudou ou cujo movimento difere entre lados; inclui valores hex e estabilidade ON/HOLD.
- `summary.json`: contagens de quatro classes de igualdade, proporções, entradas, limitações.

## Interpretação
Se o deslocamento `0x11800` apresentar taxas de igualdade maiores que controles em P1 e P2, isso prioriza a hipótese de regiões relacionadas. Se for semelhante aos controles, enfraquece-a. Dados de um único par de épocas não distinguem cópia ativa de valores coincidentes nem estabelecem periodicidade ou identidade de inimigos. Repetir com terceiro ON e deslocamento físico conhecido antes de alegar XYZ.

Acesso KSEG0 é hipótese para os dumps; a identidade da ROM e núcleo não foi verificada. Não há promoção automática de símbolos.
