# Enemy Coordinate Discovery v1.6 — Controlled Movement & Temporal Validation

## Objetivo
Nova captura P1/P2/P3 e controle de câmera, mantendo o inimigo específico visível e Bond parado durante P1→P3. Freeze ON é identificado automaticamente pela concordância de leituras virtuais KSEG0/KSEG1 do byte 0x02C90C; não são enviadas cheats ou escritas em RAM.

## Preparação
```powershell
git pull --ff-only origin main
New-Item -ItemType Directory -Force .\output\raw,.\output\csv,.\output\commands,.\output\sessions
python -m unittest tests.test_enemy_freeze_v1_6 -v
```
Abra `enemy_coordinate_controlled_capture_v1_6.lua` no Tools > Lua Console do BizHawk. Estado inicial OFF. A sonda registra automaticamente capturas `stable` após 30 frames estáveis e `hold` após 120, em cada uma das três épocas ON. Permanecer ON no mínimo 150 frames **emulados** em cada posição. Não alternar cheat durante captura. Cada conjunto de três blocos lê 29.440 bytes (região A 13.568; região B 13.568; região C 2.304), em vez de 8 MiB, e ainda assim o emulador pode pausar.

Sequência:
1. OFF, Bond parado, inimigo identificado. ON P1; aguarde `CAPTURE_hold`.
2. OFF, deixe **o mesmo inimigo** se deslocar claramente; ON P2; aguarde `CAPTURE_hold`.
3. OFF, permita outro deslocamento, preferencialmente em direção diferente; ON P3; aguarde `CAPTURE_hold`.
4. Com Freeze ON3, **sem deslocar Bond**, gire a câmera/visão. Depois registre:
```powershell
python .\tools\send_enemy_freeze_v1_6.py CAM
```
5. Confirme `CAPTURE_camera` no Lua Console e encerre:
```powershell
python .\tools\send_enemy_freeze_v1_6.py STOP
```
O script não recebe ON1/OFF1; Freeze ON/OFF é operado manualmente. `CAM` captura imediatamente a memória após a detecção do arquivo, exigindo ON3 com pelo menos 120 frames estáveis. Comandos criados exclusivamente; não reenviar `CAM` na mesma sessão.

Analisar:
```powershell
$sid=(Get-Content .\output\sessions\enemy_freeze_v1_6_session.txt).Trim()
python -m tools.analyze_enemy_freeze_v1_6 $sid
```

## Evidência e resultados
O manifesto `output/csv/enemy_freeze_v1_6_<sid>_manifest.csv` identifica frame, época, fase, janela e arquivo. Eventos e terminação são separados. Captura RAW usa hipótese KSEG0 no `System Bus`; não existe domínio RDRAM Lua confirmado no núcleo atual.
O analisador requer três épocas ON com capturas `stable` e `hold` de todas as três regiões; cada leitura deve ter mesmo frame antes/depois e tamanho exato. Relatórios criados sem substituir anteriores:
- `_temporal_fields.csv`: campos de 4/8 bytes estáveis durante ON e diferentes entre P1→P2 e P2→P3;
- `_screened_candidates.csv`: subconjunto que não mudou no controle CAM e não é cópia exatamente idêntica da região A em B;
- `_analysis.json`: totais e ressalvas.

**Limitações:** `CAM` é marcador do operador, não leitura de estado da câmera; qualquer movimentação de Bond ou inimigo torna o controle inadequado. O analisador aceita ausência de CAM, mas nesse caso `camera_control_available=false` e nenhum controle de câmera foi de fato realizado; candidatos são apenas temporais. Mudanças de bytes não comprovam XYZ, e não há identificação automatizada de instâncias nem direção espacial. O bloco C e os outros dois são hipóteses de triagem, não endereços de inimigos confirmados. A identidade exata ROM/core e o mapeamento geral KSEG0/RDRAM ainda precisam validação. Nenhum símbolo canônico é promovido.
