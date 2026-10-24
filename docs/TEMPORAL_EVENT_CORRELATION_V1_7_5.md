# Temporal Event Correlation v1.7.5

Análise **offline e somente leitura** dos arquivos originais da sessão **Spatial Position Confirmation v1.7.4**. Nenhuma nova captura ou escrita em memória. Marcadores registram o relato do operador, **não uma medição independente da movimentação de Bond**.

## Executar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_temporal_event_correlation_v1_7_5 -v
python .\tools\correlate_spatial_events_v1_7_5.py 20261024T014922Z_139431
```

O analisador cruza `_timeline.csv`, `_events.csv`, `_markers.csv`, `_termination.csv` e `_discontinuities.csv`. Confere continuidade de frames, todas as oito janelas por amostra, integridade de cada evento RAW e correspondência de BEGIN/END às fases no timeline. Rejeita sessão incompleta ou descontinuidade. Recusa sobrescrever resultados já produzidos.

## Saídas

- `spatial_v1_7_5_<session>_event_marker_distances.csv`: distância **assinada** em frames entre evento e marcador mais próximo, incluindo eventos de `NONE`. Distância negativa significa que o evento ocorreu antes do marcador.
- `_paired_offsets.csv`: coincidências no mesmo frame, emparelhamento 1:1 por distância mínima em até `--max-lag` frames (padrão quatro) e mediana da defasagem assinada B−A.
- `_repeated_joint_states.csv`: estados RAW completos dos oito campos que reaparecem em **episódios não contíguos**; não contabiliza centenas de frames de repouso como centenas de repetições.
- `_repeated_sequences.csv`: repetições exatas de N transições RAW consecutivas **dentro da série de eventos de cada endereço**, não necessariamente frames consecutivos. Padrão N=3 (`--sequence-length 3`).
- `_markers.csv`: marcadores normalizados como referência para auditoria.

Não atribuir identidade de posição, orientação ou causalidade aos resultados.

## Consultas

```powershell
$session='20261024T014922Z_139431'
$prefix=".\output\csv\spatial_v1_7_5_${session}"
Import-Csv "${prefix}_paired_offsets.csv" |
  Sort-Object {[int]$_.nearby_matches} -Descending |
  Select-Object -First 15 | Format-Table -AutoSize

Import-Csv "${prefix}_repeated_sequences.csv" |
  Where-Object { $_.offset_hex -in @('0x1F1E88','0x1F1E8C','0x1F1E90') } |
  Format-List

Import-Csv "${prefix}_event_marker_distances.csv" |
  Where-Object { $_.offset_hex -in @('0x1F1E88','0x1F1E8C','0x1F1E90') } |
  Select-Object frame,action,offset_hex,nearest_marker_label,signed_frames_from_marker |
  Format-Table -AutoSize
```

## Limitações

`nearby_matches` mede proximidade temporal com emparelhamento guloso de eventos; não identifica fonte comum. Eventos dentro de `NONE` não podem ser atribuídos a movimento/rotação. O ciclo RAW de cinco estados previamente observado é uma **hipótese de repetição**, não evidência de X/Y/Z, Auto-Aim ou ponteiros. Comparações numéricas como float/inteiro permanecem em v1.7.3 e v1.7.4.
