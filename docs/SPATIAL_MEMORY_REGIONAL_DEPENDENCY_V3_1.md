# Spatial Memory Regional Dependency Discovery v3.1

## Objetivo

Investigar dependências de atualização entre **todos os 20 blocos alinhados de 4 bytes** da janela registrada de `0x3B30B0` a `0x3B30FF` nas duas sessões v2.4 já concluídas. São **190 pares**, em **9 fases**. Trata-se de triagem descritiva, nunca de validação de coordenadas, ponteiros ou estruturas.

## Executar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_region_v3_1 -v
$original = '20261024T152944Z_311185'
$replica = '20261024T171358Z_645378'
python .\tools\analyze_spatial_region_v3_1.py $original $replica
```

O validador v2.4 exige STOP, sequência íntegra de fases e ausência de descontinuidades em **ambas** as capturas. Nenhum experimento novo no BizHawk é necessário.

## Saídas

- `spatial_v3_1_<original>__<replica>_phase_pairs.csv` — 1.710 linhas (190 pares × 9 fases).
- `spatial_v3_1_<original>__<replica>_pair_summary.csv` — 190 linhas, com média de ganhos, sincronização e número de fases.
- `spatial_v3_1_<original>__<replica>_components.csv` — 20 linhas, uma por bloco, indicando o componente resultante dos pares candidatos.

O modelo de predição usa os 4 bits de **quais bytes mudaram** no bloco de origem para prever a máscara do bloco de destino. É treinado apenas na sessão original e testado somente na réplica. Para comparação, o baseline usa apenas as frequências do alvo na sessão original. A estatística é exploratória: o modelo e os limiares não fazem correção por 190 comparações.

## Consultas

```powershell
Import-Csv ".\output\csv\spatial_v3_1_${original}__${replica}_pair_summary.csv" |
 Sort-Object { -[double]$_.mean_accuracy_gain } |
 Select-Object -First 15 left,right,mean_accuracy_gain,min_accuracy_gain,mean_logloss_gain,mean_test_sync,supported_phases,interpretation |
 Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v3_1_${original}__${replica}_pair_summary.csv" |
 Where-Object { ($_.left -eq '0x3B30D0' -and $_.right -eq '0x3B30E0') -or ($_.left -eq '0x3B30C0' -and $_.right -eq '0x3B30C4') } |
 Format-List
```

## Regras e ressalvas

Por padrão, um par vira `replicated_pair_candidate` quando apresenta **ganho de acurácia ≥ 0,02 e sincronização ≥ 0,90 em pelo menos 7 das 9 fases**. Esses valores são critérios heurísticos de triagem, não significância estatística. A orientação dos pares segue o endereço crescente; a inversão da direção pode mudar as métricas.

Os componentes são grupos por conexão transitiva entre pares candidatos: a presença em um componente **não significa** que cada par do componente esteja relacionado e **não comprova** layout ou estrutura de memória.

Os dados foram escolhidos após análises exploratórias v2.4–v3.0. As duas sessões não são uma replicação confirmatória independente das hipóteses regionais formuladas posteriormente. Não promover resultados ao `GoldenEye.mapping` sem validação direta.
