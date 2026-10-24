# Spatial Position Discovery v2.0 — Temporal & Raw Memory Audit

Esta versão examina **offline** o CSV completo de uma sessão v1.9 existente. Não depende de novo Lua, BizHawk aberto ou nova captura. Não lê, escreve ou controla memória do emulador. Os endereços `0x3B30D8` e `0x3B30D0` são **hipóteses não validadas**.

## Executar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_position_discovery_v2_0 -v
$session = '20261024T143653Z_122842'
python .\tools\analyze_spatial_position_v2_0.py $session
```

Resultados novos, **sem sobrescrever** dados nem resultados anteriores, em `output/csv/`:

| Arquivo | Conteúdo |
|---|---|
| `spatial_v2_0_<session>_phase_summary.csv` | Contagens, valores distintos, extremos float32 BE, mediana, faixa, deltas inicial-final, comprimento da maior sequência bruta constante, eventos por frame/fase |
| `spatial_v2_0_<session>_transitions.csv` | Frames exatos com mudança de bytes, valores hexadecimais antes/depois e delta float32 BE quando finito |
| `spatial_v2_0_<session>_pair_sync.csv` | Mudanças simultâneas, exclusivas e ausentes dos dois endereços em cada fase |
| `spatial_v2_0_<session>_raw_frequencies.csv` | Frequência e proporção de cada palavra hexadecimal distinta por fase/endereço |

Exemplos:

```powershell
Import-Csv ".\output\csv\spatial_v2_0_${session}_phase_summary.csv" |
  Select-Object phase,address,frames,unique_raw,transitions,longest_constant_frames,range_f32be |
  Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_0_${session}_pair_sync.csv" |
  Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_0_${session}_transitions.csv" |
  Select-Object -First 30 | Format-Table -AutoSize
```

O analisador exige STOP confirmado, dez marcadores na ordem, frames contínuos sem duplicidade e **dois endereços por frame**. Exclui da análise as amostras `PRESTART` mas mantém os originais intocados.

### Interpretação e limites

- A mudança dos bytes é observada, não inferida de arredondamento de float.
- A comparação de sincronização inclui apenas transições **dentro** da fase; fronteiras são excluídas para não atribuir a mudança à fase errada.
- `longest_constant_frames` conta amostras consecutivas de valor bruto idêntico. O período não prova imobilidade física.
- `f32be` é uma interpretação hipotética: palavras que representam inteiros, ponteiros ou flags podem assumir float32 subnormal ou números absurdamente grandes.
- Estatística por fase não verifica a movimentação efetiva do operador; `STRAFE`, `FORWARD`, `HOLD` etc. são apenas rótulos.
- Nenhuma correlação isolada permite validar uma coordenada X/Y/Z. As hipóteses continuam não canônicas.

Se o processo falhar porque arquivos v2.0 já existem, preserve-os e analise os resultados. Não é recomendado apagar automaticamente relatórios de auditoria anteriores.
