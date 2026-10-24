# Spatial Target Alignment Discovery v1.7

Primeira etapa operacional: **encontrar candidatos às coordenadas de Bond**. A identificação de soldados, do soldado mais próximo e do alvo efetivamente selecionado pelo Auto-Aim é trabalho posterior; **não é declarada como implementada**.

## Fundamento
O `GoldenEye.mapping/experiments/auto_aim/PROTOCOL.md` menciona `g_OnScreenPropList`, `best_prop` e `autoaim_target_x/y` como **hipóteses oriundas da descompilação**, sem endereços confirmados no BizHawk. Nenhum endereço nem convenção dos eixos pode ser inferido dessas denominações.

A versão 1.7 registra snapshots completos RAW de 8 MiB da RDRAM em condições marcadas, não copia ROM, não injeta comandos, não altera memória e **não infere automaticamente o alvo mais próximo**. Snapshots são locais em `output/archive/` e não devem ser enviados ao GitHub. Cada snapshot pode ocupar 8 MiB; evitar captura excessiva. O emulador pode pausar durante sua gravação.

## Preparação
1. Atualize o checkout; execute `python tools/prepare_output.py`.
2. No arquivo `spatial_target_alignment_discovery_v1_7.lua`, defina `DOMAIN="RDRAM"` e `EXPECTED_SIZE=8388608` **somente após verificar** domínio/tamanho no BizHawk; ambos começam `nil`.
3. Sem carregar savestate **durante** a sessão, abra o script na Lua Console. Para restaurar uma cena, carregue savestate antes de iniciar um novo coletor.
4. Anote hash da ROM, core do BizHawk, mapa, arma, estado do Auto-Aim e observação visual no caderno de campo. A sessão não comprova esses estados automaticamente.

## Primeiro protocolo — Bond Position
Com Bond e soldado parados e Auto-Aim mantido no mesmo estado:
```powershell
python .\tools\send_spatial_v1_7.py BOND_BASELINE
# Aguardar [spatial.v1.7] captured BOND_BASELINE
# Deslocar Bond lateralmente sem girar a câmera e soltar controles.
python .\tools\send_spatial_v1_7.py BOND_MOVE_LEFT
# Aguardar confirmação.
# Voltar à posição inicial sem girar a câmera.
python .\tools\send_spatial_v1_7.py BOND_RETURN
# Aguardar confirmação.
# Girar Bond parado, sem translação.
python .\tools\send_spatial_v1_7.py BOND_ROTATE_LEFT
# Aguardar confirmação.
python .\tools\send_spatial_v1_7.py STOP
# Confirmar FINISHED reason=stop no console Lua.
```
Cada `Request created` **não** significa que Lua capturou. O operador realiza o movimento *entre* os snapshots e aguarda a confirmação antes do próximo. Repita em uma segunda sessão deslocando Bond na direção oposta, para validar a sensibilidade à translação e à recuperação do estado inicial.

Depois de encerrada:
```powershell
$session = (Get-Content .\output\sessions\spatial_v1_7_session.txt -Raw).Trim()
python .\tools\analyze_spatial_v1_7.py $session --baseline BOND_BASELINE --movement BOND_MOVE_LEFT --rotation BOND_ROTATE_LEFT --return-label BOND_RETURN
Import-Csv ".\output\csv\spatial_v1_7_${session}_bond_position_candidates.csv" | Select-Object -First 20 | Format-Table -AutoSize
```

## Triagem de candidatos
O analisador examina palavras de 4 bytes **alinhadas** como hipóteses `float32 big-endian` e `float32 little-endian`. Ele prioriza:
- mudança entre `BOND_BASELINE` e `BOND_MOVE_LEFT`;
- pouca ou nenhuma variação entre `BOND_BASELINE` e `BOND_ROTATE_LEFT`;
- retorno aproximado ao valor de referência em `BOND_RETURN`.

Os resultados são **candidatos**, não coordenadas comprovadas. Endereços de câmera, física, NPC, HUD e valores duplicados podem satisfazer os mesmos filtros. A identificação de componentes X/Y/Z exige testes de direções ortogonais, sentidos opostos, mais de uma cena e identidade de ROM/core. Uma variação no eixo não prova unidade nem escala.

## Segurança e integridade
- Snapshot gravado em arquivo novo exclusivo e relatórios em `x`; não sobrescrever.
- `sample_index` e frames devem ser estritamente crescentes.
- Descontinuidade de frames termina a captura antes de aceitar novos snapshots.
- O analisador recusa sessão não encerrada, snapshot ausente/incompleto e descontinuidade.
- Sem memória validada para Bond/soldado, o cálculo de distância ou ângulo permanece bloqueado.
- O `GoldenEye.mapping` recebe apenas candidatos com a proveniência documentada; nenhuma promoção automática.

## Escopo seguinte
Após validar posição de Bond: obter lista e identidade individual dos soldados, distinguir soldados elegíveis de objetos não combatentes, testar coordenadas individuais com movimento/repetição e, somente então, calcular distância e testar a escolha efetiva do Auto-Aim. O soldado mais próximo não é necessariamente o alvo do jogo.

## Testes
```powershell
python -m unittest tests.test_spatial_target_alignment_v1_7 -v
```
