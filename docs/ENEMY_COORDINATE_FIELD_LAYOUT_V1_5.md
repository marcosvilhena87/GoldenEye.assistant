# Enemy Coordinate Discovery v1.5 — Field Alignment & Record Layout Validation

## Objetivo
Comparar possíveis registros com stride de `0x40`, `0x48` ou `0x50` e controles próximos `0x44`, `0x4C`, `0x54`, separando campos alinhados de 2, 4 e 8 bytes. São hipóteses exploratórias, não estruturas nem coordenadas validadas.

## Entradas
Os quatro dumps brutos existentes da sessão `20261024T210536Z_648577`, dois para cada época ON. As regiões A `[0x0D5000,0x0D8500)` e B=`A+0x11800` são avaliadas independentemente. Os dumps precisam ter exatamente 8 MiB, os metadados devem indicar estado ON e mesmo frame antes/depois.

## Método
Um campo é marcado estável se seus bytes inteiros são iguais entre ON STABLE e ON HOLD em P1 e P2. É dinâmico quando o campo muda de P1 para P2. Para cada stride e largura, são comparados campos alinhados no endereço absoluto e separados por exatamente esse stride.

Cada par estável contabiliza: se ambos mudam; se os bytes de P1 coincidem; e se os bytes de P2 coincidem. As comparações de igualdade são byte a byte por palavra, sem reinterpretar floats nem pressupor eixo espacial. `exact_both_epoch_rate` é o **mínimo das duas taxas de coincidência**, e não a taxa de pares idênticos simultaneamente em P1/P2. Controles também podem representar periodicidades reais.

A avaliação por campos inteiros evita interpretar cada byte de um float como evidência independente. Posições da fase são residuais módulo stride, relativas ao início da janela de cada região, e não constituem identificação de layout.

## Como executar
```powershell
git pull --ff-only origin main
python -m unittest tests.test_enemy_freeze_v1_5 -v
$sid="20261024T210536Z_648577"
python -m tools.analyze_enemy_freeze_v1_5 $sid
```

## Resultados
- `output/csv/enemy_freeze_v1_5_<sid>_field_stride_ranking.csv` — 36 linhas, A/B, 6 strides e 3 larguras;
- `output/csv/enemy_freeze_v1_5_<sid>_field_phase_profiles.csv` — frequências por fase;
- `output/csv/enemy_freeze_v1_5_<sid>_summary.json` — proveniência e limitações.

Os relatórios não sobrescrevem resultados anteriores. Nenhum endereço é promovido no `GoldenEye.mapping`. A validação de coordenadas requer inimigo identificado, direção de movimento conhecida, terceira posição e repetição intersessões.
