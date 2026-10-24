# Spatial Position Discovery v2.1 — Memory Layout & Temporal Pattern Investigation

Análise **offline** dos dados brutos de uma sessão v1.9, usando a validação estrutural da v2.0. Nenhuma nova coleta, leitura do emulador ou edição do catálogo canônico é realizada.

## Preparação

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_position_discovery_v2_1 -v
$session='20261024T143653Z_122842'
python .\tools\analyze_spatial_position_v2_1.py $session
```

Os quatro CSVs novos são gerados em `output/csv` sem sobrescrever relatórios já existentes:

- `spatial_v2_1_<session>_layouts.csv`: por fase/endereço, estatísticas das interpretações `uint32`, `int32`, `float32` em big/little endian, metades `uint16`/`int16` e bytes individuais. Estatísticas numéricas descartam NaN/Inf mas mantêm o número de valores distintos.
- `spatial_v2_1_<session>_lag_patterns.csv`: similaridade da palavra hexadecimal e concordância de mudanças em lags de 1 a 32 frames. Similaridade alta em um lag é um *indício de periodicidade*, não evidência de posição.
- `spatial_v2_1_<session>_byte_activity.csv`: alterações de cada um dos quatro bytes, diversidade, moda hexadecimal e sua frequência.
- `spatial_v2_1_<session>_cross_lag.csv`: concordância temporal de mudanças nos dois endereços, em lags de −32 a +32 frames. Mudanças simultâneas podem refletir atividade geral do jogo, não uma estrutura compartilhada.

```powershell
Import-Csv ".\output\csv\spatial_v2_1_${session}_layouts.csv" |
 Where-Object { $_.phase -eq 'BASELINE_HOLD' } |
 Select-Object address,interpretation,unique,changes,longest_run,min,max |
 Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_1_${session}_lag_patterns.csv" |
 Where-Object { $_.phase -eq 'BASELINE_HOLD' } |
 Sort-Object { -[double]$_.raw_equal_rate } |
 Select-Object -First 20 | Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_1_${session}_byte_activity.csv" |
 Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_1_${session}_cross_lag.csv" |
 Where-Object { $_.phase -eq 'BASELINE_HOLD' } |
 Sort-Object { -[double]$_.change_agreement_rate } |
 Select-Object -First 15 | Format-Table -AutoSize
```

Parâmetro opcional `--max-lag 64` (de 1 a 1024). Os cálculos de lag não atravessam marcadores de fase. `PRESTART` fica excluído das métricas e os CSVs originais permanecem intactos.

## Limitações

Os dados v1.9 foram coletados somente nos endereços `0x3B30D8` e `0x3B30D0`. É possível verificar padrões temporais e interpretações desses 8 bytes, **mas não identificar limites de estruturas próximas, apontadores ou buffers reutilizados** sem ampliar a janela de memória em nova captura. Este relatório não atribui endereço X/Y/Z e não prova causalidade entre os dois campos.
