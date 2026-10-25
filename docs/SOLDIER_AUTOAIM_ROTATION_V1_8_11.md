# Soldier Coordinate Discovery v1.8.11 — Auto-Aim Rotation Isolation

## Objetivo
Investigar a resposta dos campos experimentais de Bond a uma rotacao proxima ao Soldier #1 congelado, separando o teste com auto-aim ligado/desligado. Nenhum endereço se torna coordenada X/Z validada apenas por esta coleta.

## A: retrospectiva sem nova coleta
A sessao da v1.8.10 ja possui BOND_STOP_NEAR, BOND_ROTATE e BOND_STOP_FAR:
```powershell
git pull --ff-only origin main
python -m unittest tests.test_soldier_autoaim_v1_8_11 -v
python -m tools.analyze_soldier_autoaim_v1_8_11 20261025T173358Z_23230 --source v1.8.10
$r=Get-Content ".\output\csv\soldier_autoaim_v1_8_11_v1_8_10_20261025T173358Z_23230_analysis.json" -Raw | ConvertFrom-Json
$r.fields.GetEnumerator() | Out-Null
$r.fields.'0x06D248'.BOND_ROTATE
$r.fields.'0x06D250'.BOND_ROTATE
$r.fields.'0x20F594'.BOND_ROTATE
```
Sem estado ON/OFF verificado, essa analise retrospectiva NAO atribui a variacao ao auto-aim.

## B: novo teste ON/OFF
Execute a partir da raiz do repositorio e prepare `output/csv`, `output/commands`, `output/sessions`. Carregue `soldier_autoaim_rotation_v1_8_11.lua` na Lua Console. Os marcadores nao alteram as configuracoes nem os cheats; operador deve alterar auto-aim manualmente em opcoes do jogo e confirmar cada estado. Manter o Freeze dos inimigos durante toda a captura.

Envie um comando por vez com `python -m tools.send_soldier_autoaim_v1_8_11 LABEL`, aguardando `MARKED`. Registrar pelo menos 120 frames por fase e evitar caminhar durante a rotacao.

1. BASELINE — Bond parado e soldado identificado visualmente.
2. FREEZE_REQUEST_ON — ativar Freeze manualmente.
3. FREEZE_CONFIRMED — confirmar visualmente soldado imovel.
4. AIM_ON_STILL — auto-aim ativado e Bond parado.
5. AIM_ON_ROTATE — girar Bond sem deslocamento.
6. AIM_ON_SETTLE — parar Bond.
7. AIM_OFF_REQUEST — mudar auto-aim para OFF manualmente.
8. AIM_OFF_CONFIRMED — confirmar nas opcoes.
9. AIM_OFF_STILL — Bond parado.
10. AIM_OFF_ROTATE — mesma rotacao, idealmente mesmo angulo e ponto fisico.
11. AIM_OFF_SETTLE — Bond parado.
12. STOP — encerrar e confirmar DONE stop.

```powershell
$sid=(Get-Content ".\output\sessions\soldier_autoaim_v1_8_11_session.txt" -Raw).Trim()
python -m tools.analyze_soldier_autoaim_v1_8_11 $sid
$r=Get-Content ".\output\csv\soldier_autoaim_v1_8_11_v1_8_11_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.fields.'0x06D248'
$r.fields.'0x06D250'
$r.distance_candidates
```

## Criterios
Comparar spread e delta assinado de cada campo nos estados parado/giro ON e OFF, mais constancia dos candidatos de Soldier #1 em ambos os testes. Ausencia de flag de auto-aim na RDRAM, giro angular nao calibrado, movimento residual ou diferenca de posicao inicial podem confundir o contraste. Mesmo spread menor com OFF e apenas evidência associativa, nao causal. Repetir com ordem invertida OFF/ON e outro save para corroborar. O mapeamento canonico nao deve ser alterado.
