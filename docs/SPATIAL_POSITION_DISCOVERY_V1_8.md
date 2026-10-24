# Spatial Position Discovery v1.8

Busca nova em **toda a RDRAM de 8 MiB**, em vez de restringir-se aos oito endereços v1.7.4. Os 14 snapshots são acionados pelo operador e capturados somente após confirmação no console Lua. As etiquetas representam a intervenção declarada; **a v1.8 não lê independentemente o controle do jogador e não confirma por si só que Bond se moveu**.

## Instalação

```powershell
git pull --ff-only origin main
python .\tools\prepare_output.py
python -m unittest tests.test_spatial_position_discovery_v1_8 -v
```

No `spatial_position_discovery_v1_8.lua` configure os dois valores **após verificar o domínio no BizHawk**:
```lua
local DOMAIN="RDRAM"
local EXPECTED_SIZE=8388608
```

Carregue o script Lua do repositório no BizHawk. Não carregar savestates enquanto uma sessão estiver ativa. Mantenha a mesma partida, câmera inicial e cenário, sem inimigos atrapalhando, se possível. São 14 capturas de 8 MiB (cerca de 112 MiB de arquivos binários). **Não adicionar snapshots RAW ao Git.**

## Protocolo sequencial

Para cada estado, use:
```powershell
python .\tools\send_spatial_v1_8.py BASELINE_STILL
```
**Aguardar `captured BASELINE_STILL` no console Lua**. Após cada nova captura, enviar **somente** o próximo comando. O sender impõe a seguinte ordem e rejeita comandos fora de sequência:

| Ordem | Comando | Condição física antes de capturar |
|---|---|---|
| 1 | BASELINE_STILL | Bond parado, sem girar |
| 2 | LEFT_MID | Bond se deslocou lateralmente para esquerda, ponto intermediário |
| 3 | LEFT_END | Mesmo deslocamento, mais à esquerda |
| 4 | LEFT_HOLD | Controles soltos, Bond imóvel no ponto esquerdo |
| 5 | RIGHT_MID | Voltou parcialmente à direita |
| 6 | RIGHT_END | Retornou perto do ponto inicial |
| 7 | RIGHT_HOLD | Parado após retorno |
| 8 | FORWARD_MID | Avançou, ponto intermediário |
| 9 | FORWARD_END | Avançou mais, sem girar |
| 10 | FORWARD_HOLD | Parado após avançar |
| 11 | BACK_MID | Recuou parcialmente |
| 12 | BACK_END | Voltou perto do ponto de início longitudinal |
| 13 | BACK_HOLD | Parado após recuar |
| 14 | ROTATE_END | Girou sem deslocamento desde BACK_HOLD |

Depois:
```powershell
python .\tools\send_spatial_v1_8.py STOP
```
O coletor só aceita STOP após as 14 capturas. `Request created` indica somente fila de comandos; `captured` confirma captura, **não valida intervenção manual**.

## Análise

```powershell
$session=(Get-Content .\output\sessions\spatial_v1_8_session.txt -Raw).Trim()
python .\tools\analyze_spatial_position_v1_8.py $session
Import-Csv ".\output\csv\spatial_v1_8_${session}_coordinate_candidates.csv" |
 Select-Object -First 30 offset_hex,endianness,classification,left_delta,right_delta,forward_delta,back_delta,rotation_error |
 Format-Table -AutoSize
```

O analisador percorre todas as palavras alinhadas de 4 bytes, em hipóteses float32 BE e LE, sem corte arbitrário Top-100. Requer variação progressiva em ao menos um par de direções inversas, estabilidade nas paradas e pouca variação entre BACK_HOLD e ROTATE_END. Ordena os candidatos que respondem aos dois pares primeiro. A validação de tipo RAW/inteiro permanece uma etapa posterior. O uso de `--min-delta` (padrão 0.01) e tolerâncias é uma **heurística**, não unidade conhecida da engine.

`two_axes_unverified` significa somente que **um campo** mostrou respostas às duas intervenções ortogonais declaradas: não prova dois eixos independentes nem vetor XYZ. Posições verdadeiras com baixa escala, representações inteiras, deslocamento irregular, câmera móvel ou cenário que progrida entre capturas podem ser omitidas. Nenhum endereço deve ser promovido ao catálogo canônico sem validações independentes.
