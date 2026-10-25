# Bond Position v1.8.15 — Alias Update Ordering & Frame-Lag Validation

Auditoria **offline** do CSV da captura v1.8.13. Não requer outro script Lua ou nova sessão.

## Iniciar
```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_alias_v1_8_15 -v
$sid = "20261025T181441Z_9591"
python -m tools.audit_bond_alias_v1_8_15 $sid
$r=Get-Content ".\output\csv\bond_alias_v1_8_15_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.divergence_count
$r.ordering_counts | Format-List
$r.phase_summary | Format-List
$r.divergence_frames | Select-Object frame,phase,one_frame_ordering,resynchronized_next_frame,matched_adjacent | Format-Table -AutoSize
```

## Interpretação
Usa pares de componentes como **vetores RAW conjuntos**:
- A = `0x06D248/0x06D250`.
- B = `0x0D33EC/0x0D33F4`.

Uma divergência é registrada quando os vetores RAW no mesmo frame são diferentes. O relatório examina mudanças desde o frame anterior e reencontro com o valor oposto no próximo frame. Somente eventos em que A e/ou B mudam entram em `change_events`, evitando que frames imóveis dominem a comparação. Os grupos por fase registram atualizações de ambas ou de apenas uma região.

`A_first` ou `B_first` indica **um padrão observacional compatível** com atualização em frames consecutivos, não ordem interna comprovada no código do jogo. Outros casos são `not_demonstrated`. Um frame de divergência pode ter ambas as componentes divergentes; o script compara vetores completos.

## Limites
Não existe gravação dos comandos reais do controle, rastreamento independente de entidades ou acesso aos instantes internos de escrita na RDRAM. O resultado não valida eixos físicos nem autoriza alterar o GoldenEye.mapping como verdade estabelecida.
