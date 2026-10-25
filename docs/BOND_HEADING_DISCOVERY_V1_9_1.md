# Bond Heading Discovery v1.9.1 — Direction Vector & Angular Representation Validation

## Evidência e hipóteses
A sessão v1.9 de 21.126 frames, SID \`20261025T192036Z_63794\`, mostrou que \`0x0D33F8\` conserva o novo valor após TURN_LEFT (variação float32 BE +1.80052), depois TURN_RIGHT (−1.79239), enquanto TURN_FULL_CIRCLE termina próximo da orientação inicial (+0.00115). Isso sugere estado persistente associado a giro; não comprova heading nem seno/cosseno. \`0x0D3998\` e \`0x0D3D40\` exibem transientes que retornam aos respectivos valores de base. 

## A — Auditoria retrospectiva (sem nova coleta)
\`\`\`powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_v1_9_1 -v
$sid="20261025T192036Z_63794"
python -m tools.analyze_bond_heading_v1_9_1 $sid --source v1.9
$r=Get-Content ".\output\csv\bond_heading_v1_9_1_v1_9_\${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.complete
$r.fields.'0x0D33F8' | Format-List
$r.vector_pair_hypotheses | Select-Object -First 10 | Format-Table
$r.related_probe_differences | Format-Table
\`\`\`
A auditoria preserva ordem das fases, direção dos passos \`up_steps/down_steps\`, máximo salto e variações numéricas. Compara potenciais pares do vetor em \`0x0D33F0/0x0D33F8/0x0D33FC/0x0D3400/0x0D3404\` calculando espalhamento de \`x²+y²\`, sem validar uma identidade trigonométrica somente pelo ranking. Inclui pares relacionados separados por \`0x3A8\`.

## B — Nova captura direcionada
Abra \`bond_heading_discovery_v1_9_1.lua\` na Lua Console do BizHawk, estando na raiz do repositório. Crie \`output/csv\`, \`output/commands\`, \`output/sessions\` se necessário. Sem Freeze e sem escrita na memória pelo coletor. Evite salvar/carregar state enquanto a Lua está ativa.

Envie um marcador por vez com \`python -m tools.send_bond_heading_v1_9_1 LABEL\`, aguardando confirmação \`MARKED\`; mantenha 120+ frames nos controles de imobilidade.

Fases, em ordem:
1. \`BASELINE_STILL\`: parada e orientação conhecida por ponto fixo.
2. \`TURN_LEFT_SHORT\`: pequeno giro à esquerda, sem caminhar.
3. \`HOLD_LEFT\`: parar, registrar referência visual.
4. \`TURN_RIGHT_RETURN\`: retornar visualmente à direção inicial.
5. \`HOLD_RETURN\`: parar.
6. \`TURN_LEFT_QUARTER\`: girar aproximadamente 90°, pela referência visual.
7. \`HOLD_QUARTER\`: parar.
8. \`TURN_LEFT_HALF\`: continuar aproximadamente mais 90°.
9. \`HOLD_HALF\`: parar.
10. \`TURN_LEFT_FULL\`: completar a volta até a orientação original (aproximadamente 180° adicionais).
11. \`HOLD_FULL\`: parar.
12. \`TURN_RIGHT_FULL\`: executar outra volta aproximadamente completa no sentido oposto.
13. \`HOLD_FINAL\`: parar.
14. \`MOVE_FORWARD_NO_TURN\`: mover sem girar, controle de translação.
15. \`HOLD_MOVE\`: parar.
16. \`STOP\`: encerrar.
O protocolo usa ângulos aproximados e não os considera medidas independentes de graus.

\`\`\`powershell
$sid=(Get-Content ".\output\sessions\bond_heading_v1_9_1_session.txt" -Raw).Trim()
python -m tools.analyze_bond_heading_v1_9_1 $sid --source v1.9.1
$r=Get-Content ".\output\csv\bond_heading_v1_9_1_v1_9_1_\${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.complete
$r.fields.'0x0D33F8' | Format-List
$r.vector_pair_hypotheses | Select-Object -First 10 | Format-Table
\`\`\`

## Portas de validação
Requeremos: sentido de giro oposto com progressão consistente; continuidade ou wrap-around angular identificado; retorno numérico após volta visualmente confirmada; sinal invariante durante translação; componente ortogonal com norma \`x²+y²\` estável *durante o giro*; reprodução noutra sessão; ROM/núcleo verificados. \`x²+y²≈1\` por si só não identifica função seno/cosseno; endereços que variam somente durante comando podem descrever câmera, arma ou animação. Não promover ainda para GoldenEye.mapping.
