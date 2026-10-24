# Spatial Memory Community Cross-Validation v3.3

## Objetivo

Reavaliar as arestas da v3.2 em duas subamostras **cronológicas** da sessão de replicação, comparando a generalização temporal e controles nulos por **rotação circular do alvo dentro de cada fase e metade**. Foco nas comunidades estatísticas do grupo de 13 blocos e nas fases FORWARD / P1_HOLD. Não comprova coordenadas, causalidade ou estrutura interna do GoldenEye.

## Executar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_community_cv_v3_3 -v
$original='20261024T152944Z_311185'
$replica='20261024T171358Z_645378'
python .\tools\analyze_spatial_community_cv_v3_3.py $original $replica
```

As capturas devem existir localmente e ter STOP íntegro, sequência completa de fases e nenhum salto de frame. São necessários os CSVs `_edges.csv` e `_communities.csv` da v3.2 para as sessões informadas.

## Método

1. Congela os pares **diretos** selecionados pelo critério v3.2 (45 pares na execução conhecida).
2. Para cada par e fase, treina o classificador de máscara de alteração exclusivamente nos dados da **sessão original**.
3. Testa sem reajustar o modelo nas metades **early** e **late** (em ordem cronológica) da sessão de replicação.
4. Em cada metade, executa por padrão até 19 rotações circulares distintas da variável-alvo com deslocamentos superiores a três eventos, mantendo o preditor fixo. Calcula um p empírico unilateral **exploratório** separado para ganho de acurácia e ganho de log-loss.
5. Resume diferenças entre metades e entre comunidades. Pares cujos extremos estejam em comunidades distintas recebem `cross_community`.

Os controles preservam frequências marginais e parte da autocorrelação, mas não preservam necessariamente dependências globais nem independência entre eventos.

**Ressalva crítica:** os pares foram escolhidos usando a segunda sessão na v3.2; reavaliar metades dessa mesma sessão não é confirmação independente, mesmo com treinamento apenas na primeira. Os p empíricos são descritivos, não corrigidos por seleção, autocorrelação nem múltiplas comparações. Padrões interessantes exigem **terceira captura pré-planejada**, não ajustes retroativos destes dados.

## Saídas

- `_phase_holdouts.csv`: 45 pares × 9 fases × 2 metades = **810 linhas**, se os 45 pares originais persistirem no arquivo;
- `_community_summary.csv`: duas linhas por categoria de comunidade presente (early e late);
- `_shift_null.csv`: até 19 controles por cada holdout (tipicamente 15.390 linhas);
- `_pair_summary.csv`: uma linha por par direto (tipicamente 45).

Arquivos de saída são protegidos contra sobrescrita.

## Consultas PowerShell

```powershell
Import-Csv ".\output\csv\spatial_v3_3_${original}__${replica}_community_summary.csv" |
 Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v3_3_${original}__${replica}_phase_holdouts.csv" |
 Where-Object { $_.phase -in @('FORWARD','P1_HOLD') } |
 Group-Object community,test_segment,phase |
 ForEach-Object { [pscustomobject]@{Group=$_.Name;N=$_.Count;MeanGain=(($_.Group | Measure-Object accuracy_gain -Average).Average)} } |
 Format-Table -AutoSize
```

O `GoldenEye.mapping` continua inalterado.
