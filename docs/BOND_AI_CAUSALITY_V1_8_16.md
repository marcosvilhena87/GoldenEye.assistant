# GoldenEye Bond–AI Causality v1.8.16 — Controlled Freeze/Release

## Hipótese
B = 0x0D33EC / 0x0D33F4: candidato a posição física de Bond; A = 0x06D248 / 0x06D250: candidato a posição conhecida pela IA. A v1.8.15 encontrou precedência B → A em 11 frames divergentes. O operador relatou que congelar B impede deslocamento de Bond, e congelar A faz o soldado perseguir o local antigo. **Ambos os fatos são evidências preliminares, não prova conclusiva de relações internas.**

## Preparação e segurança experimental
```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_ai_causality_v1_8_16 -v
New-Item -ItemType Directory -Force output\csv,output\commands,output\sessions | Out-Null
```
Abra BizHawk a partir da raiz do repositório, crie um savestate de recuperação e inicie `bond_ai_causality_v1_8_16.lua` na Lua Console. A Lua é **somente leitura**; o Freeze é controlado **manualmente** pelo operador via RAM Watch/Cheats.

### Endereços
- Congele **somente** A `0x06D248` e `0x06D250` para o tratamento.
- **Não congele** B `0x0D33EC` e `0x0D33F4` durante o tratamento: esses endereços são a variável independente de movimento observada.
- Registre explicitamente que cada Freeze está ligado/desligado e mantenha outros cheats constantes.
- Identifique o mesmo soldado visível e remova obstáculos relevantes quando possível. Reinicie do mesmo savestate antes da repetição.

## Fases (enviar uma por vez)
Use `python -m tools.send_bond_ai_causality_v1_8_16 LABEL` e aguarde `MARKED` na Lua Console antes do próximo comando. Manter pelo menos 120 frames por fase de observação.

1. BASELINE: imóvel e com A e B sem Freeze.
2. CONTROL_MOVE: caminhar sem nenhum dos quatro campos congelado.
3. CONTROL_SOLDIER_RESPONSE: parar e verificar se o soldado procura a posição atual.
4. RESET_ORIGIN: restaurar estado/posição inicial para tratamento; revalidar o soldado.
5. AI_FREEZE_REQUEST: congelar somente A (dois endereços) manualmente.
6. AI_FREEZE_CONFIRMED: confirmar A travado na RAM Watch; deixar B livre.
7. DECOUPLE_MOVE: deslocar Bond da posição inicial A até nova posição B.
8. DECOUPLE_BOND_STILL: manter Bond parado na nova posição.
9. SOLDIER_OLD_TARGET: observar se o soldado segue o ponto anterior, sem mover Bond.
10. AI_RELEASE_REQUEST: remover o Freeze de A.
11. AI_RELEASE_CONFIRMED: confirmar A livre na RAM Watch.
12. BOND_STILL_POST_RELEASE: manter Bond imóvel e observar se os dois vetores passam a coincidir.
13. SOLDIER_RETARGET_OBSERVED: anotar se o soldado agora se dirige à posição atual de Bond.
14. REPEAT_RESET: restaurar mesmo savestate e condições.
15. REPEAT_AI_FREEZE: congelar somente A e confirmar.
16. REPEAT_MOVE: repetir deslocamento e observação do ponto antigo.
17. REPEAT_RELEASE: liberar A sem mover Bond.
18. REPEAT_RETARGET: observar perseguição ao novo ponto.
19. STOP: terminar.

Aguardar `DONE stop` no console. O marcador SOLDIER_RETARGET_OBSERVED é anotação do operador: o script não classifica automaticamente intenções da IA.

## Análise
```powershell
$sid=(Get-Content ".\output\sessions\bond_ai_causality_v1_8_16_session.txt" -Raw).Trim()
python -m tools.analyze_bond_ai_causality_v1_8_16 $sid
$r=Get-Content ".\output\csv\bond_ai_causality_v1_8_16_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.complete
$r.freeze_phase_A_constant
$r.bond_still_after_release_B_constant
$r.phase_frame_counts
$r.phase_numeric_stats | Format-List
```

## Critério de interpretação
A condição de causalidade é apoiada se A permanece numericamente estável durante deslocamento de B, o soldado segue o alvo antigo, A volta a acompanhar B após liberação com Bond imóvel, e o soldado muda de alvo sem movimento adicional de Bond. A evidência deve ser reproduzida e comparada ao controle sem Freeze.

**Não** promover automaticamente A como 'AI Target Position' definitivamente estabelecido ou B como X/Z físicos. Pode ser uma cópia consultada por diversos subsistemas.
