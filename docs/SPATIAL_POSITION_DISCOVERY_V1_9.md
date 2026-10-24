# Spatial Position Discovery v1.9 — Candidate Validation

Validação independente **somente de leitura**, sem controlar Bond nem modificar RDRAM. Candidatos da v1.8:

- `0x3B30D8` — float32 big endian, **não validado**.
- `0x3B30D0` — float32 big endian, **não validado**.

O coletor amostra ambos os endereços a cada frame, registrando valor bruto hexadecimal e float32 big endian. As fases são rótulos informados pelo operador: **não provam que Bond se deslocou**. As métricas não transformam hipóteses em coordenadas canônicas.

## Preparação

```powershell
git pull --ff-only origin main
python .\tools\prepare_output.py
python -m unittest tests.test_spatial_position_discovery_v1_9 -v
```

Inspecione o domínio no BizHawk, depois configure no início de `spatial_position_discovery_v1_9.lua`:

```lua
local DOMAIN="RDRAM"
local EXPECTED_SIZE=8388608
```

Inicie esse Lua no BizHawk. Não use savestates durante a sessão. O script limita-se a 54.000 frames e interrompe-se em descontinuidades detectadas da contagem de frames.

## Sequência: sinalizar antes de executar cada intervenção

Em outro PowerShell, para cada fase envie `python .\tools\send_spatial_v1_9.py ETIQUETA`. **Aguarde `[spatial.v1.9] marked ETIQUETA`** no console Lua antes de executar a intervenção física. Deixe cada fase rodar por vários segundos, de modo a registrar a ação e a transição. Ao alterar para a fase de imobilidade, solte os comandos imediatamente após receber o marcador. O sender exige ordem e reconhecimento de cada marcador.

| Ordem | Etiqueta | Ação após confirmação do marcador |
|---|---|---|
| 1 | `BASELINE_HOLD` | Bond imóvel, câmera estável |
| 2 | `FORWARD` | Caminhar para frente, sem girar |
| 3 | `FORWARD_HOLD` | Soltar controles, ficar parado |
| 4 | `BACK` | Caminhar para trás na direção inicial |
| 5 | `BACK_HOLD` | Ficar parado |
| 6 | `ROTATE` | Girar horizontalmente **sem caminhar** |
| 7 | `ROTATE_HOLD` | Parar o giro, sem movimentar |
| 8 | `STRAFE` | Movimentar lateralmente sem mudar orientação |
| 9 | `STRAFE_HOLD` | Ficar parado |
| 10 | `STOP` | Finalizar o registro |

Exemplo:

```powershell
python .\tools\send_spatial_v1_9.py BASELINE_HOLD
# aguarde "marked BASELINE_HOLD"; mantenha Bond imóvel por alguns segundos
python .\tools\send_spatial_v1_9.py FORWARD
# aguarde "marked FORWARD"; avance por alguns segundos
python .\tools\send_spatial_v1_9.py FORWARD_HOLD
```

Não envie dois comandos sem a confirmação de `marked`. `Request created` confirma apenas arquivo em fila. Os arquivos CSV são criados em `output/csv/`; não os comite nem adicione dumps binários ao Git.

## Analisar

Após o console imprimir `FINISHED ... reason=stop`:

```powershell
$session=(Get-Content .\output\sessions\spatial_v1_9_session.txt -Raw).Trim()
python .\tools\analyze_spatial_position_v1_9.py $session
Import-Csv ".\output\csv\spatial_v1_9_${session}_validation.csv" | Format-Table -AutoSize
```

A análise exige as dez fases na ordem correta, STOP confirmado, pelo menos três amostras válidas por fase/endereço e nenhuma descontinuidade. Calcula deltas de ida/volta, faixa dos holds, efeito da rotação e retorno à referência, de maneira heurística. Categorias possíveis: `candidate_reproduced_unverified`, `rotation_sensitive_unverified`, `directional_only_unverified`, `rejected_by_observations`. Nenhuma classificação constitui validação definitiva. A amplitude da rotação e o erro de retorno exigem interpretação cuidadosa, assim como a eventual influência de câmera, animação e entidades vizinhas.
