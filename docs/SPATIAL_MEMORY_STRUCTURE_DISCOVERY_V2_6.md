# Spatial Memory Structure Discovery v2.6

Auditoria offline somente leitura dos três endereços-base `0x3B30D0`, `0x3B30E0` e `0x3B30EC`, utilizando a captura bruta da sessão v2.4. Não inicia nova captura, não modifica memória, não usa savestates e não altera `GoldenEye.mapping`. Endereços não validados.

## Executar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_structure_v2_6 -v
$session = '20261024T152944Z_311185'
python .\tools\analyze_spatial_structure_v2_6.py $session
```

Arquivos CSV em `output/csv/spatial_v2_6_<session>_*.csv`: `bytes` (atividade de cada byte), `split16` (duas metades alinhadas em BE/LE), `synchrony` (coincidência e phi para pares de bytes relativos), `periodicity` (lags 1,2,3,6,13,19) e `patterns` (palavras de 32 bits, alternância A-B-A). Os arquivos preexistentes não são sobrescritos.

## Consultar

```powershell
Import-Csv ".\output\csv\spatial_v2_6_${session}_bytes.csv" |
  Where-Object phase -eq 'P0_HOLD' |
  Select-Object base,byte_address,change_rate,unique_values,longest_constant_run | Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_6_${session}_synchrony.csv" |
  Where-Object phase -eq 'P0_HOLD' |
  Sort-Object { -[double]$_.synchrony_given_either } |
  Select-Object -First 15 left,right,synchrony_given_either,phi,value_equal_fraction | Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_6_${session}_periodicity.csv" |
  Where-Object { $_.phase -eq 'P0_HOLD' -and $_.lag -in @('6','13','19') } |
  Sort-Object { -[double]$_.excess_match } |
  Select-Object -First 15 address,lag,raw_match_rate,independent_match_baseline,excess_match | Format-Table -AutoSize
```

## Interpretação e limitações

A coincidência de alterações não demonstra uma estrutura comum ou um eixo espacial. O coeficiente phi compara apenas os eventos mudou/não mudou; denominador zero é exibido vazio. O baseline de correspondência independente dos valores por lag é uma referência descritiva, não um teste de periodicidade estatisticamente corrigido. Uma sequência A-B-A pode refletir alternância, atualização interna ou ruído. Comparar metades de 16 bits não estabelece automaticamente a estrutura dos dados nem endianness.

O carregamento exige o STOP validado, ordem dos marcadores, ausência de descontinuidades e bytes completos em todos os frames. Nenhuma interpretação é promovida ao catálogo canônico.
