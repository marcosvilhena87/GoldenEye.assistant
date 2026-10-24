# Spatial Data Type Validation v1.7.3

Investigação somente leitura sobre **oito snapshots originais de RDRAM** (quatro de cada sessão). Mantém intactas as capturas e os CSVs v1.7.1/v1.7.2.

## Execução — PowerShell

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_data_types_v1_7_3 -v
python .\tools\validate_spatial_data_types_v1_7_3.py 20261024T012117Z_46365 20261024T012527Z_57819
```

O analisador confere os manifestos e terminações por meio da validação da v1.7.1. Lê todos os offsets incluídos no `_strict_candidates.csv` da v1.7.2 e acrescenta as sondas prioritárias mesmo que não estejam na lista. Não presume identidade de Bond ou formato de dados. Arquivos brutos jamais devem ser enviados ao GitHub.

## Saídas exclusivas e imutáveis
- `spatial_v1_7_3_<left>_vs_<right>_raw_values.csv`: oito observações para cada offset, contendo RAW, float32 BE/LE, int32 BE/LE e uint32 BE/LE.
- `spatial_v1_7_3_<left>_vs_<right>_type_audit.csv`: diferenças de bytes nos quatro estados de cada sessão, deltas sob as várias interpretações, tipos float normal/subnormal/zero/infinito/NaN, e avaliação estrita de retorno/rotação por igualdade dos bytes.
- `spatial_v1_7_3_<left>_vs_<right>_priority_review.csv`: as mesmas análises para os endereços prioritários, incluindo 0x2EC5D4, 0x2E1480 e 0x285264.

```powershell
$left='20261024T012117Z_46365'
$right='20261024T012527Z_57819'
$prefix=".\output\csv\spatial_v1_7_3_${left}_vs_${right}"
Import-Csv "${prefix}_type_audit.csv" | Group-Object classification | Select-Object Name,Count | Format-Table -AutoSize
Import-Csv "${prefix}_priority_review.csv" |
  Select-Object session,offset_hex,raw_baseline,raw_moved,raw_return,raw_rotation,changed_bytes_move,changed_bytes_return,changed_bytes_rotation,classification,status |
  Format-Table -AutoSize
```

## Interpretação responsável
A igualdade RAW no retorno ou rotação é uma observação **mais estrita** que a tolerância numérica, mas não prova identidade física nem descarta coordenadas com ruído ou quantização. Valores float32 subnormais na representação alternativa não invalidam automaticamente o formato verdadeiro; as classificações são descritivas. Inteiros e floats aplicados sobre os mesmos quatro bytes podem ambos produzir números finitos sem demonstrar a codificação verdadeira. Mudanças feitas entre snapshots não são observadas continuamente.

## Escopo
Não altera a coleta Lua, não calcula distâncias, não localiza soldados nem faz escrita em RDRAM. Identificação e validação de coordenadas continuam pendentes.
