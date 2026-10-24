# Spatial Memory Shared Source Discovery v2.8

Analisa a gravação bruta v2.4, para os três blocos experimentais de quatro bytes `0x3B30D0`, `0x3B30E0` e `0x3B30EC`. A análise é **offline, read-only** e não altera o catálogo `GoldenEye.mapping`. Nenhuma identificação espacial é inferida automaticamente.

## Executar
```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_shared_source_v2_8 -v
$session = '20261024T152944Z_311185'
python .\tools\analyze_spatial_shared_source_v2_8.py $session
```

Três arquivos são criados em `output/csv` sem sobrescrever anteriores:

| Arquivo | Métricas |
|---|---|
| `spatial_v2_8_<session>_block_sync.csv` | Atualização de blocos completos, bitmasks dos bytes alterados, coeficiente phi, mudanças coincidentes, controle circular |
| `spatial_v2_8_<session>_value_dependency.csv` | Relação observada entre valores brutos de quatro bytes, ambiguidade das associações, pares mais frequentes |
| `spatial_v2_8_<session>_joint_events.csv` | Transições simultâneas, padrões mais frequentes e fração de eventos conjuntos |

```powershell
Import-Csv ".\output\csv\spatial_v2_8_${session}_block_sync.csv" |
 Where-Object { $_.left -eq '0x3B30D0' -and $_.right -eq '0x3B30E0' } |
 Select-Object phase,phi,sync_given_either,byte_mask_equal_fraction,shared_changed_byte_fraction,empirical_one_sided_p |
 Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_8_${session}_value_dependency.csv" |
 Where-Object { $_.left -eq '0x3B30D0' -and $_.right -eq '0x3B30E0' } |
 Select-Object phase,distinct_left,distinct_right,distinct_pairs,forward_determinism,reverse_determinism,modal_pair_fraction |
 Format-Table -AutoSize
```

## Limitações e critérios

Os arquivos reportam 3 pares de blocos × 9 fases, ou seja, 27 registros em cada relatório. A sincronização multibyte não prova que as variáveis pertençam à mesma estrutura. `forward_determinism` e `reverse_determinism` são consistências **dentro da mesma amostra**, que podem chegar a 1 simplesmente quando há valores quase todos únicos; não são testes preditivos fora da amostra. Examine `distinct_left`, `distinct_right` e `distinct_pairs` antes de interpretar os índices.

O controle circular é determinístico e utiliza até 199 deslocamentos não próximos de zero. Preserva a sequência interna de uma das séries, mas não estabelece causalidade e não corrige múltiplas comparações. Padrões de transições simultâneas podem representar atualizações comuns, mas também processos relacionados sem uma fonte única.

Leitura de dados exige STOP confirmado, fases completas e ausência de descontinuidade na captura v2.4. Endereços continuam experimentais; nenhuma alteração canônica automática.
