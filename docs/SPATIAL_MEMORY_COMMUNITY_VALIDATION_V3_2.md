# Spatial Memory Community Validation v3.2

Auditoria offline das **190 relações** e **nove fases** que já constam no CSV `phase_pairs.csv` da v3.1. Não depende de novas capturas, não altera o jogo e não valida coordenadas nem estruturas canônicas.

## Executar no PowerShell
```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_communities_v3_2 -v
$original = '20261024T152944Z_311185'
$replica = '20261024T171358Z_645378'
python .\tools\analyze_spatial_communities_v3_2.py $original $replica
```

Requer o CSV v3.1 existente: `output/csv/spatial_v3_1_<original>__<replica>_phase_pairs.csv`. O analisador valida exatamente 190 pares × 9 fases, sem duplicatas, com IDs de sessões consistentes. Não sobrescreve saída anterior.

## Relatórios

| Arquivo | Conteúdo |
|---|---|
| `_edges.csv` | 190 pares, conexão direta segundo critérios de triagem e bitmap de nove fases |
| `_communities.csv` | 20 blocos, componente por conectividade e subcomunidade por aglomeração gulosa de modularidade |
| `_sensitivity.csv` | Cinco cenários de limiares predefinidos, tamanho de componentes e Jaccard com referência |
| `_phase_persistence.csv` | Nove fases, arestas ativas em cada uma e sobreposição com o grafo de referência |
| `_ranking.csv` | 190 pares ordenados pelo número de fases com suporte e ganho médio de acurácia |

## Consultas
```powershell
Import-Csv ".\output\csv\spatial_v3_2_${original}__${replica}_sensitivity.csv" | Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v3_2_${original}__${replica}_phase_persistence.csv" |
 Select-Object phase,total_supported_edges,baseline_edges_supported,baseline_edge_fraction | Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v3_2_${original}__${replica}_communities.csv" |
 Sort-Object { [int]$_.component }, { [int]$_.community }, block |
 Select-Object block,component,community,size,internal_edges,external_edges,members | Format-Table -AutoSize -Wrap
```

## Método e limites

**Aresta direta**: uma relação que satisfaz `accuracy_gain >= 0.02` e `test_sync >= 0.90` em pelo menos 7 das 9 fases. **Conexão transitiva**: blocos relacionados por um caminho de arestas, sem necessidade de aresta direta entre eles. As comunidades são produzidas por fusões determinísticas com incremento positivo da modularidade do grafo não ponderado; são subagrupamentos descritivos, não estruturas de memória identificadas.

**Sensibilidade**: são examinadas combinações `(gain, sync, phases)` de `(0, 0.85, 6)`, `(0.02, 0.90, 7)`, `(0.05, 0.90, 7)`, `(0.02, 0.95, 7)` e `(0.02, 0.90, 9)`. Jaccard compara conjuntos de arestas e não mede significância estatística.

**Controles estatísticos**: esta versão apresenta a distribuição/ranking observados para os 190 pares, mas **não calcula p-valores nem correção por múltiplos testes**, porque as fases e pares são altamente dependentes e os mesmos dados foram usados para selecionar hipóteses. Um teste confirmatório de excepcionalidade exige nova captura independente e uma estratégia de controle nulo previamente definida. Não chamar candidatos de significativos nem promover endereços ao `GoldenEye.mapping`.
