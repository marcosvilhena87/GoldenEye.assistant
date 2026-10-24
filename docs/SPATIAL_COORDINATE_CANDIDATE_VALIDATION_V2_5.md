# Spatial Coordinate Candidate Validation v2.5

A v2.5 avalia **somente** os três endereços-base indicados pela v2.4: `0x3B30D0`, `0x3B30E0` e `0x3B30EC`. Os resultados continuam experimentais; não modifica o `GoldenEye.mapping`.

## Execução

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_position_discovery_v2_5 -v
$session='20261024T152944Z_311185'
python .\tools\analyze_spatial_position_v2_5.py $session
```

A v2.5 lê a captura **bruta** `output/csv/spatial_v2_4_<session>_window.csv` e os registros de marcadores, descontinuidades e término. Não sobrescreve relatórios preexistentes e não inicia nenhuma captura.

Os arquivos de saída são `output/csv/spatial_v2_5_<session>_phase_summary.csv` (métricas temporais por fase) e `output/csv/spatial_v2_5_<session>_candidate_checks.csv` (verificação por endereço/interpretação). São avaliadas interpretações de 16 e 32 bits, incluindo IEEE 754 big/little endian para 32 bits.

```powershell
Import-Csv ".\output\csv\spatial_v2_5_${session}_candidate_checks.csv" |
 Select-Object address,interpretation,step1,step_back,step2,return_error,rotation_shift,status,evidence_against |
 Format-Table -AutoSize -Wrap
```

## Critérios e limitações

O comparador usa as medianas e MADs dos últimos 120 frames de cada HOLD, mede trajetórias quadro a quadro nas nove fases e verifica reversibilidade do primeiro deslocamento, estabilidade relativa nas pausas, invariância durante rotação e resposta no segundo deslocamento. `no_second_forward_shift_in_this_field` **não elimina necessariamente uma coordenada de eixo individual**, pois a rotação pode tornar o segundo movimento perpendicular àquele eixo.

Uma classificação `experimental_support` indica somente cumprimento de heurísticas na sessão, nunca prova espacial. Um movimento manual pode ser irregular ou os marcadores podem não coincidir perfeitamente com o instante de início de movimento. Taxas de transição não demonstram causalidade e diferenças na endianness não são observações independentes. Os campos não alinhados e endereços fora da janela não são examinados.

Para validação real, será necessária reprodução controlada e evidência de continuidade e movimento direcional correlacionado, com registro explícito das limitações.
