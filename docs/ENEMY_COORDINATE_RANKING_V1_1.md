# Enemy Coordinate Discovery v1.1 — Candidate Ranking & Spatial Structure Discovery

## Objetivo
Analisar **todos** os candidatos nos dumps congelados da v1, sem limitar aos primeiros 300 do JSON. Classificar offsets, detectar agrupamentos físicos por proximidade e encontrar pares de offsets. Classificações são heurísticas de triagem, **não probabilidade de coordenada XYZ**.

## Entradas
Usa o manifesto `output/csv/enemy_freeze_v1_<session>_manifest.csv` e os quatro dumps `on_stable` e `on_hold` das primeiras duas épocas ON completas. Cada dump tem 8 MiB. Exige registros com `frame == frame_after` e `raw_bus_kseg0_unvalidated`; não sobrescreve os resultados originais.

## Executar
```powershell
git pull --ff-only origin main
python -m unittest tests.test_enemy_freeze_v1_1 -v
$sid="20261024T210536Z_648577"
python .\tools\analyze_enemy_freeze_v1_1.py $sid
```

## Saídas
Em `output/csv/`, com prefixo `enemy_freeze_v1_1_<sid>`:
- `candidate_ranking.csv`: todas as interpretações que satisfazem estabilidade exata em P1, P2 e diferença de pelo menos 1e-5, ambas float32 endianidades; magnitude finita menor que 1e7.
- `spatial_clusters.csv`: grupos de offsets, aceitando até 64 bytes de distância entre **offsets consecutivos**. Um grupo não implica um único objeto.
- `candidate_pairs.csv`: pares de offsets distintos até 16 bytes de distância, mesma interpretação endian; **não são eixos comprovados**.
- `summary.json`: proveniência, totais, limitações e caminhos.

O score é explícito: +2 se delta entre 0.001 e 10.000 e ambos os valores têm magnitude até 100.000; +1.5 por vizinho até 4 vizinhos a ±16 bytes; +0.25 por vizinho até 12 vizinhos a ±64 bytes; +1 para big-endian. Não há calibração empírica que fundamente preferir big-endian além de prioridade exploratória. Uma diferença numérica insignificante ou uma leitura instável entre snapshots descarta a interpretação. Isso cria falsos negativos.

## Validação necessária depois da triagem
Exigir pelo menos três posições congeladas, deslocamentos conhecidos em dois eixos, Bond parado e controle com rotação. Isolar o mesmo inimigo durante as medições, testar instâncias múltiplas e repetição entre sessões. Averiguar se KSEG0 cobre corretamente a RDRAM para os endereços selecionados, verificar ROM SHA/core e somente depois considerar símbolo no `GoldenEye.mapping`.

**Não** utilizar candidatos para automação do Auto-Aim/Auto-Shot enquanto não houver mapeamento físico robusto.
