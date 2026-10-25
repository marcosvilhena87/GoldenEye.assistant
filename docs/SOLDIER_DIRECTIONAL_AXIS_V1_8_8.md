# Soldier Coordinate Discovery v1.8.8 — Directional Axis Identification

Somente leitura. Busca variacao direcional de campos experimentais, **nao atribui X/Z automaticamente**. Regioes monitoradas sao as mesmas da v1.8.7, incluindo 0x20F594, 0x20F5AC e pares duplicados.

## Preparacao
Atualize com `git pull --ff-only origin main`; crie `output/csv`, `output/commands`, `output/sessions`. Carregue `soldier_directional_axis_v1_8_8.lua` na Lua Console, executando a partir da raiz do repositorio. RDRAM deve ter 8 MiB.

## Sequencia experimental
Use `python -m tools.send_soldier_direction_v1_8_8 LABEL`, **um comando por vez** e aguarde `MARKED` no BizHawk. Mantenha pelo menos 120 frames em cada fase e documente a posicao/identidade visual do mesmo Soldier #1.

1. `BASELINE`: Bond e Soldier #1 imoveis.
2. `BOND_ROTATE`: girar Bond sem translacao, soldado parado.
3. `BOND_MOVE`: deslocar Bond, soldado parado.
4. `AXIS_A_POS`: deslocar somente Soldier #1 na direcao A+ escolhida visualmente.
5. `AXIS_A_NEG`: deslocar o mesmo soldado na direcao oposta A-.
6. `AXIS_B_POS`: deslocar o mesmo soldado em uma direcao perpendicular B+.
7. `AXIS_B_NEG`: deslocar na direcao oposta B-.
8. `AXIS_A_REPEAT`: repetir A+ para testar sinal de variacao.
9. `STATIONARY`: confirmar visualmente ambos imoveis.
10. `STOP`: terminar; aguardar `DONE stop`.

**Importante:** sem controle confiavel de movimento do soldado, os rotulos A/B nao garantem deslocamentos direcionais. Marcar a fase nao automatiza o movimento. Registre se foi observado movimento correto. Os snapshots sequenciais tambem acumulam preparacao/transicao; por isso a interpretacao deve ser conservadora.

## Analisador
```powershell
$sid = (Get-Content ".\output\sessions\soldier_direction_v1_8_8_session.txt" -Raw).Trim()
python -m tools.analyze_soldier_direction_v1_8_8 $sid
$r = Get-Content ".\output\csv\soldier_direction_v1_8_8_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.capture_complete
$r.missing_phases
$r.candidates | Select-Object -First 30 offset_hex,format,axis_a_opposition,axis_b_opposition,axis_a_perpendicular_ratio,axis_b_perpendicular_ratio,stationary_quiet | Format-Table -AutoSize
```

Analisador compara sinais opostos, relacao de variacao entre eixos, quietude na fase imovel, repeticao A+ e controles Bond; so interpreta float32 alinhado BE/LE. Nao calcula coordenadas absolutas, dimensoes de mundo ou identidade RAM. Repetir em novo save usando nova sessao para teste independente.
