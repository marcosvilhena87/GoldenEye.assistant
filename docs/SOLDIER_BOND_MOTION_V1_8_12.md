# Soldier Coordinate Discovery v1.8.12 — Bond Rotation vs Translation Discrimination

Experimento observacional de leitura de RDRAM em GoldenEye N64 / BizHawk. Mantem o Soldier #1 visualmente identificado sob Freeze e separa as respostas numéricas dos candidatos de Bond durante rotações e caminhadas. **Não registra entrada do controle nem orientacao física calibrada**: os marcadores são anotações do operador.

## Atualização e instalação

```powershell
git pull --ff-only origin main
python -m unittest tests.test_soldier_motion_v1_8_12 -v
New-Item -ItemType Directory -Force output\csv,output\commands,output\sessions | Out-Null
```

Carregue `soldier_bond_motion_v1_8_12.lua` na Lua Console, a partir da raiz do repositório. O script monitora aproximadamente os mesmos 107 campos experimentais anteriores; RAM somente leitura e requisito de 8 MiB.

## Protocolo

Use `python -m tools.send_soldier_motion_v1_8_12 LABEL` para enviar um marcador por vez, confirmando `MARKED` antes do próximo e observando pelo menos 120 frames por fase. Aplique manualmente o Freeze e mantenha-o ativo até STOP. Para maior rigor, mantenha auto-aim na mesma configuração durante todas as fases e evite colisões.

1. BASELINE: Bond e soldado inicialmente parados.
2. FREEZE_REQUEST_ON: ativar Freeze dos inimigos.
3. FREEZE_CONFIRMED: confirmar visualmente o soldado imóvel.
4. STILL_BEFORE: Bond parado; sem ação.
5. ROTATE_LEFT: girar no próprio lugar à esquerda, sem comandos direcionais de caminhada.
6. STILL_AFTER_LEFT: parar completamente.
7. ROTATE_RIGHT: girar no próprio lugar à direita, idealmente retornando orientação.
8. STILL_AFTER_RIGHT: parar completamente.
9. TRANSLATE_FORWARD: avançar sem alterar intencionalmente o ângulo de visão.
10. STILL_AFTER_FORWARD: parar completamente.
11. TRANSLATE_BACK: recuar mantendo a direção de visão.
12. STILL_AFTER_BACK: parar completamente.
13. ROTATE_REPEAT: repetir a rotação no mesmo lugar.
14. STILL_FINAL: parar completamente.
15. STOP: encerrar. Confirmar no console `DONE stop`.

## Análise

```powershell
$sid=(Get-Content ".\output\sessions\soldier_motion_v1_8_12_session.txt" -Raw).Trim()
python -m tools.analyze_soldier_motion_v1_8_12 $sid
$r=Get-Content ".\output\csv\soldier_motion_v1_8_12_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.capture_complete
$r.candidate_pairs | Format-List
$r.fields.'0x06D248' | Format-List
$r.fields.'0x06D250' | Format-List
$r.raw_alias_equalities | Format-List
```

Análise calcula delta inicial/final, amplitude máxima, mudanças, caminho acumulado por fase, distâncias candidatas bidimensionais calculadas nos mesmos frames, estabilidade byte a byte dos campos congelados nas fases e igualdade de aliases em toda a sessão. Controles STILL fornecem referência de ruído do experimento. Se houver mudanças em ROTATE sem TRANSLATE, não inferir diretamente que são ângulo ou câmera; pode ocorrer deslocamento residual. Se houver respostas em TRANSLATE, não afirmar XYZ sem referencial espacial independente. Nenhuma promoção automática ao GoldenEye.mapping.
