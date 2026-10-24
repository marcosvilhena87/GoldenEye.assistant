# Spatial Coordinate Candidate Validation v1.7.2

Esta etapa refina os **5.238 candidatos publicados pela v1.7.1** sem alterar os snapshots nem seus relatórios. Não atribui significado físico ou identidade de Bond aos endereços.

## Executar no PowerShell

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_coordinates_v1_7_2 -v
python .\tools\validate_spatial_coordinates_v1_7_2.py 20261024T012117Z_46365 20261024T012527Z_57819
```

Resultados exclusivos em `output/csv/spatial_v1_7_2_<left>_vs_<right>_*`:
- `_strict_candidates.csv`: inclui aprovados e rejeitados com proporções, motivos e classe.
- `_adjacent_groups.csv`: grupos de 2+ palavras consecutivas (4 bytes) da mesma endianidade; adjacência não comprova vetor X/Y/Z.
- `_duplicate_patterns.csv`: grupos com **padrões numéricos exatamente iguais** para as variações e erros observados, não comprova alias, ponteiro ou identidade.
- `_priority_review.csv`: endereços 0x286124, 0x286128, 0x28612C, 0x2863A4, 0x2863A8, 0x2863AC, 0x286CEC, 0x286CF0, 0x286CF4 e 0x3B2BD4..0x3B2BDC quando presentes na entrada v1.7.1.

## Critérios

Para cada sessão:
- Movimento com módulo mínimo `0.01` (hipótese numérica configurável, **não unidade do jogo**).
- Razão `abs(rotation_delta)/abs(movement_delta) <= 0.05`.
- Razão `abs(return_error)/abs(movement_delta) <= 0.10`.

Isso corrige o falso positivo conhecido por tolerância absoluta (quando delta de rotação tem a mesma ordem de grandeza da mudança por movimento). Porém, pode produzir falsos negativos caso um campo de posição real tenha escala muito pequena. Parametrize usando `--min-movement`, `--max-rotation-ratio` e `--max-return-ratio` (positivos e finitos). A classificação é apenas **heurística**; não elimina necessidade de novas experiências.

## Exibir resultados

```powershell
$left='20261024T012117Z_46365'
$right='20261024T012527Z_57819'
$prefix=".\output\csv\spatial_v1_7_2_${left}_vs_${right}"
Import-Csv "${prefix}_strict_candidates.csv" |
  Group-Object status | Select-Object Name,Count | Format-Table -AutoSize
Import-Csv "${prefix}_priority_review.csv" |
  Select-Object offset_hex,endianness,delta_left,delta_right,ratio_rotation_left,ratio_rotation_right,strict_both,status |
  Format-Table -AutoSize
Import-Csv "${prefix}_adjacent_groups.csv" |
  Where-Object { [int]$_.strict_members -ge 2 } |
  Select-Object -First 30 | Format-Table -AutoSize
```

Não há novas capturas nesta etapa. É uma pós-análise dos CSVs existentes. Para conferir candidatos fora do conjunto triado na v1.7.1, é necessário voltar aos snapshots brutos.

**Limitação deliberada:** não identifica automaticamente coordenadas de soldado, do soldado mais próximo, nem alvo do Auto-Aim.
