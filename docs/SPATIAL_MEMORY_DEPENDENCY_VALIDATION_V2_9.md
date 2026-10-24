# Spatial Memory Dependency Validation v2.9

Ferramenta offline de análise exploratória das relações entre os blocos `0x3B30D0`, `0x3B30E0` e `0x3B30EC` na sessão de captura v2.4. Não abre o BizHawk, não grava memória e não valida coordenadas nem atualiza `GoldenEye.mapping`.

## Execução
```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_dependency_v2_9 -v
$session = '20261024T152944Z_311185'
python .\tools\analyze_spatial_dependency_v2_9.py $session
```

Arquivos gerados sem sobrescrita em `output/csv`: `spatial_v2_9_<session>_out_of_sample.csv` e `spatial_v2_9_<session>_conditional_transitions.csv`.

## Como são feitos os testes

Cada um dos três pares de blocos é avaliado nos dois sentidos. Variáveis-alvo testadas: palavra bruta de quatro bytes (`raw_word`) e bitmask dos bytes que mudaram desde o frame anterior (`change_mask`). A partição 70/30 divide temporalmente cada fase, sem embaralhar frames. Um segundo teste treina em `P0_HOLD` e avalia separadamente em cada uma das outras oito fases.

O modelo-base sempre prevê o valor mais comum do treino. O modelo condicional usa a frequência mais comum do alvo para cada valor de origem visto no treino e recorre ao modelo-base quando a origem não foi vista. Para log-loss é usada suavização que preserva uma probabilidade não nula para categorias inéditas. Ganhos de acurácia e log-loss positivos significam melhor desempenho condicional fora da amostra; não demonstram causalidade. A saída também inclui Brier aproximado para o evento da classe observada, que **não** é um Brier multiclasse completo.

`seen_fraction` é indispensável para interpretar os resultados: valores de origem quase sempre inéditos podem tornar a transferência inviável. Métricas dentro das fases são avaliações cronológicas, e a generalização `P0_HOLD` → demais fases não substitui replicação com outra sessão independente.

## Inspecionar
```powershell
Import-Csv ".\output\csv\spatial_v2_9_${session}_out_of_sample.csv" |
 Where-Object { $_.left -eq '0x3B30D0' -and $_.right -eq '0x3B30E0' } |
 Select-Object feature,train_phase,test_phase,seen_fraction,baseline_accuracy,conditional_accuracy,accuracy_gain,logloss_gain |
 Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_9_${session}_conditional_transitions.csv" |
 Where-Object { $_.phase -eq 'P0_HOLD' -and $_.left -eq '0x3B30D0' -and $_.right -eq '0x3B30E0' } |
 Sort-Object { -[double]$_.count } | Select-Object -First 15 | Format-Table -AutoSize
```

## Limitações

Previsão dentro da mesma sessão não constitui validação espacial. Forte sincronização pode existir sem relação direta entre valores. Transições condicionais de bitmask são agregadas por fase; elas não são usadas como evidência independente da avaliação preditiva. Uma queda no log-loss não comprova a estrutura da memória. Sem atualizações canônicas automáticas.
