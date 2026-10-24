# Spatial Position Confirmation v1.7.4

Monitoramento temporal **somente leitura**, a cada frame do emulador, de oito endereços *candidatos*:

`0x05FCB4`, `0x05FCD4`, `0x0D61C4`, `0x0E79C4`, `0x1F1E88`, `0x1F1E8C`, `0x1F1E90`, `0x2EBCE4`.

Selecionados da interseção de estabilidade RAW nas sessões esquerda/direita v1.7.3. Não são coordenadas validadas. Não são interpretados diretamente como direção de arma, alvo ou posição.

## Preparação

```powershell
git pull --ff-only origin main
python .\tools\prepare_output.py
python -m unittest tests.test_spatial_position_v1_7_4 -v
```

No Lua `spatial_position_confirmation_v1_7_4.lua`, após confirmar domínio e tamanho no BizHawk: configurar `DOMAIN="RDRAM"` e `EXPECTED_SIZE=8388608`. O coletor recusa execução sem configuração. Iniciar novo script pelo Lua Console, na raiz do repositório.

Não restaurar savestate com captura ativa. Se precisar reiniciar uma cena, carregar primeiro e então abrir uma nova sessão Lua. Confirmar cada `marked` no console antes de iniciar ou terminar uma intervenção.

## Protocolo de captura

Enviar um comando por vez, sempre aguardando o reconhecimento:

```powershell
python .\tools\send_spatial_v1_7_4.py BEGIN_REST_BASELINE
# Permanecer parado
python .\tools\send_spatial_v1_7_4.py END_REST_BASELINE

python .\tools\send_spatial_v1_7_4.py BEGIN_MOVE_LEFT
# Movimentar-se para a esquerda sem girar a câmera
python .\tools\send_spatial_v1_7_4.py END_MOVE_LEFT
python .\tools\send_spatial_v1_7_4.py BEGIN_REST_AFTER_LEFT
# Soltar os controles
python .\tools\send_spatial_v1_7_4.py END_REST_AFTER_LEFT

python .\tools\send_spatial_v1_7_4.py BEGIN_MOVE_RIGHT
# Movimentar-se para a direita sem girar a câmera
python .\tools\send_spatial_v1_7_4.py END_MOVE_RIGHT
python .\tools\send_spatial_v1_7_4.py BEGIN_REST_AFTER_RIGHT
python .\tools\send_spatial_v1_7_4.py END_REST_AFTER_RIGHT

python .\tools\send_spatial_v1_7_4.py BEGIN_MOVE_FORWARD
# Movimentar-se para frente sem girar a câmera
python .\tools\send_spatial_v1_7_4.py END_MOVE_FORWARD
python .\tools\send_spatial_v1_7_4.py BEGIN_REST_AFTER_FORWARD
python .\tools\send_spatial_v1_7_4.py END_REST_AFTER_FORWARD

python .\tools\send_spatial_v1_7_4.py BEGIN_MOVE_BACK
# Movimentar-se para trás sem girar a câmera
python .\tools\send_spatial_v1_7_4.py END_MOVE_BACK
python .\tools\send_spatial_v1_7_4.py BEGIN_REST_AFTER_BACK
python .\tools\send_spatial_v1_7_4.py END_REST_AFTER_BACK

python .\tools\send_spatial_v1_7_4.py BEGIN_ROTATE_ONLY
# Girar parado, sem deslocamento
python .\tools\send_spatial_v1_7_4.py END_ROTATE_ONLY
python .\tools\send_spatial_v1_7_4.py BEGIN_REST_AFTER_ROTATION
python .\tools\send_spatial_v1_7_4.py END_REST_AFTER_ROTATION

python .\tools\send_spatial_v1_7_4.py STOP
```

**Cuidado:** O usuário deve esperar o texto `marked BEGIN_...` **antes de movimentar Bond**, e o `marked END_...` **antes de qualquer outra intervenção**. `Request created` do PowerShell só confirma que o arquivo de comando existe. A captura é contínua inclusive fora dos intervalos marcados, sob ação `NONE`. Para tempos curtos, pode-se iniciar com apenas REST_BASELINE, MOVE_LEFT, REST_AFTER_LEFT e ROTATE_ONLY, encerrando os intervalos.

## Análise

```powershell
$session=(Get-Content .\output\sessions\spatial_v1_7_4_session.txt -Raw).Trim()
python .\tools\analyze_spatial_position_v1_7_4.py $session
Import-Csv ".\output\csv\spatial_v1_7_4_${session}_temporal_audit.csv" |
  Select-Object action,offset_hex,samples,raw_changes,float_be_delta,float_be_steps_up,float_be_steps_down,float_le_delta |
  Format-Table -AutoSize
```

`_timeline.csv` contém os oito RAW de cada frame. `_events.csv` contém suas alterações. `_markers.csv`, `_termination.csv`, `_discontinuities.csv` e `_manifest.csv` permitem auditoria de integridade. O analisador escreve somente um arquivo adicional `_temporal_audit.csv` sem substituir qualquer resultado anterior; recusa marcadores incompletos, descontinuidades, frames ausentes e encerramento com ação aberta.

Uma coordenada real pode mudar ao longo do movimento e permanecer constante no repouso, mas **essa observação não comprova posição de Bond**, tipo de dado, eixo ou escala. Só se valida após múltiplos contrastes com referenciais físicos independentes e ROM/core confirmados.

## Escopo

Não identifica soldados, distâncias, alvo de Auto-Aim e não escreve na memória do emulador.
