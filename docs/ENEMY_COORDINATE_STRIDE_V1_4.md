# Enemy Coordinate Discovery v1.4 — Record Stride & Structure Layout Discovery

## Objetivo
Comparar hipóteses de periodicidade `0x40,0x48,0x50,0x60,0x80` (64,72,80,96,128 bytes), com deslocamentos próximos `0x44,0x4C,0x54,0x64,0x84` como controles. Aplicar às regiões A `[0x0D5000,0x0D8500)` e B `A+0x11800`, usando os mesmos quatro dumps ON/ON HOLD.

## Método
Primeiro, cada byte vira um marcador binário 1 apenas se permanece estável de ON STABLE a ON HOLD em ambas as épocas, e seu valor muda de P1 a P2. Para um stride S, mede pares de marcadores ativos a uma distância S, e distribui-os por resíduo módulo S. A taxa observada e razão de enriquecimento contra expectativa marginal (A_ativos * B_ativos / pares) são medidas descritivas; bytes vizinhos são correlacionados, portanto **não representam teste de significância nem evidência de stride de registro por si só**.

A mesma análise é executada em ambas as regiões. O ranking ordena pelo menor enriquecimento entre as duas. A análise não compara direções de movimento nem conhece instâncias de inimigos. Um stride alto no ranking serve apenas para selecionar um próximo teste físico. A correspondência de valores, agrupamento em registros e modelo de layout ainda não estão validados.

## Execução
```powershell
git pull --ff-only origin main
python -m unittest tests.test_enemy_freeze_v1_4 -v
$sid="20261024T210536Z_648577"
python -m tools.analyze_enemy_freeze_v1_4 $sid
```

## Saídas em `output/csv`
- `enemy_freeze_v1_4_<sid>_stride_ranking.csv` — contagens/razões e enriquecimento em A/B por hipótese.
- `enemy_freeze_v1_4_<sid>_phase_profiles.csv` — frequência de marcadores dinâmicos por posição relativa ao stride em cada região.
- `enemy_freeze_v1_4_<sid>_summary.json` — proveniência, totais e ressalvas.

Arquivos anteriores não são sobrescritos. A função chamada `same_change` no relatório representa **duas posições com marcação dinâmica**, não igualdade dos seus deltas numéricos. As hipóteses e os controles são exploratórios; `0x50` não recebe peso preferencial. Sem terceiro ON e ground truth espacial, não promover símbolos em `GoldenEye.mapping`.
