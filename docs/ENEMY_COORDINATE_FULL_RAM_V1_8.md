# Enemy Coordinate Discovery v1.8 — Full RAM Coordinate Search & Graphics-Aware Filtering

## Escopo
Nova sessão com 3 épocas ON de Freeze em posições sucessivas do mesmo inimigo, dois snapshots integrais por época e um snapshot CAM final. Cada snapshot tem 8 MiB (hipótese de leitura KSEG0 `0x80000000..0x807FFFFF` via `System Bus`), não memória física RDRAM confirmada. O capturador apenas lê o emulador e escreve arquivos; não altera RAM nem ativa/desativa cheat.

## Preparação
```powershell
git pull --ff-only origin main
New-Item -ItemType Directory -Force .\output\raw,.\output\csv,.\output\commands,.\output\sessions
python -m unittest tests.test_enemy_freeze_v1_8 -v
```
Carregue `enemy_coordinate_full_ram_capture_v1_8.lua` no Lua Console do BizHawk. **Não reutilize CAM ou STOP da sessão anterior.** A sonda cria SID novo. Faça P1 ON durante ao menos 120 frames emulados e aguarde `CAPTURE_hold`; depois OFF para mover o inimigo com Bond parado, P2 ON e aguarde HOLD, OFF para segundo movimento, P3 ON e aguarde HOLD. Se possível, registre em notas separadas o alvo visual, mapa, direção de cada deslocamento e câmera. Não mudar cheats durante um dump. Captura 8 MiB byte a byte pode bloquear momentaneamente a emulação; acompanhe o Lua Console.

Depois de P3 HOLD, com Freeze ON, gire a visão **sem deslocar Bond**, e então:
```powershell
python .\tools\send_enemy_freeze_v1_8.py CAM
```
Aguarde `CAPTURE_camera`; encerre:
```powershell
python .\tools\send_enemy_freeze_v1_8.py STOP
```
`ON1`, `ON2` e `ON3` não são comandos do Python: alternância Freeze é manual.
Para análise:
```powershell
$sid=(Get-Content .\output\sessions\enemy_freeze_v1_8_session.txt).Trim()
python -m tools.analyze_enemy_freeze_v1_8 $sid
Import-Csv ".\output\csv\enemy_freeze_v1_8_${sid}_float_candidates.csv" | Where-Object review_priority -eq "review" | Select-Object -First 30 | Format-Table -AutoSize
Import-Csv ".\output\csv\enemy_freeze_v1_8_${sid}_nearby_groups.csv" | Select-Object -First 30 | Format-Table -AutoSize
```

## Análise
Valida metadados de seis snapshots obrigatórios, integridade temporal de frame e tamanho exatamente 8 MiB. CAM é opcional, porém ausência marca controle indisponível. Percorre endereços **alinhados a 4 bytes** dos 8 MiB. Exige estabilidade ON versus HOLD em P1/P2/P3 e mudança de bytes nas duas transições; tenta float32 BE e LE e retém valores finitos de magnitude menor que 1e6 com mudanças de pelo menos 1e-4 e no máximo 1e5. Limiares heurísticos sem escala física validada.

Para cada interpretação, `graphics_context` detecta sequências de opcodes de display lists em janela local de 64 bytes; `camera_changed` marca mudança P3→CAM. Ambos são **alertas, não exclusões permanentes**. Forma agrupamentos de três palavras float32 próximas com distâncias 4 ou 8 bytes, sem nomear eixos XYZ.

Resultados exclusivos em `output/csv`: `enemy_freeze_v1_8_<sid>_float_candidates.csv`, `_nearby_groups.csv`, `_analysis.json`. Não sobrescreve nenhuma captura nem resultado existente.

## Limitações críticas
Mesmo uma tripla numérica com trajetória suave não prova posição de inimigo. A ROM, core, equivalência KSEG0→RDRAM, escala e sinal dos eixos não foram confirmados. O marcador CAM não verifica a ação do operador. O detector gráfico é específico a hipóteses de comandos de microcódigo e pode ter falsos positivos; os dados brutos são mantidos. O scan total é por palavras de 4 bytes alinhadas, **não** todos os offsets desalinhados, nem outros tipos numéricos. Para validar XYZ: identificar o alvo e suas três posições físicas, direção conhecida e repetir em sessão independente.
