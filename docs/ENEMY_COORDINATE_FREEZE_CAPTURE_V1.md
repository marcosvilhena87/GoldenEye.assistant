# Enemy Coordinate Discovery v1 — Freeze-Synchronized Memory Capture

## Base conhecida
Experimento Freeze Address Mapping v1.1: 9.006 frames, 4.878 OFF e 4.128 ON; transições observadas nos frames 738457 (OFF→ON), 741272 (ON→OFF), 743177 (OFF→ON), todas confirmadas 29 frames depois; KSEG0 e KSEG1 em concordância; nenhum erro de leitura. Esses dados vieram do console do operador, não são capturas desta nova sonda.

## Objetivo
Capturar bytes de memória em períodos ON estáveis e após deslocamentos OFF, para **procurar candidatos**, não afirmar XYZ de inimigos. RAM Watch exibe `0x02C90C` em domínio `RDRAM`, mas a API Lua do núcleo atual só expõe `System Bus`. Leitura virtual KSEG0 `0x8002C90C` e KSEG1 `0xA002C90C` acompanha Freeze; não se demonstrou tradução física geral de todo o bloco de RAM.

## Procedimento
1. Na pasta do repositório, executar:
```powershell
git pull --ff-only origin main
New-Item -ItemType Directory -Force .\output\raw,.\output\commands,.\output\csv,.\output\sessions
```
2. Deixar Bond **parado** em cenário com inimigo ativo. Freeze inicialmente **OFF**; abrir `enemy_coordinate_freeze_capture_v1.lua` no Tools > Lua Console do BizHawk. **O script lê 8 MiB por snapshot, podendo deixar o emulador temporariamente sem resposta**. Não alternar o Freeze durante a captura.
3. Alterar manualmente o Freeze na ordem OFF → ON (P1) → OFF (mover inimigo) → ON (P2). Recomenda-se opcionalmente OFF → ON (P3). Cada ON deve durar pelo menos 150 frames emulados. Cada OFF deve durar tempo suficiente para o inimigo se deslocar. Confirmar no RAM Watch.
4. A sonda registra um `on_stable` ao detectar 30 frames ON consecutivos e outro `on_hold` após 120 frames. Cada nova fase OFF tem `off_stable` após 30 frames. Não envia input/cheat nem savestates.
5. Encerrar após pelo menos duas fases ON completas:
```powershell
python .\tools\send_enemy_freeze_v1.py STOP
$sid=(Get-Content .\output\sessions\enemy_freeze_v1_session.txt).Trim()
python .\tools\analyze_enemy_freeze_v1.py $sid
```
6. Compartilhar `output/csv/enemy_freeze_v1_<id>_manifest.csv`, `_events.csv`, `_termination.csv` e o arquivo `_candidates.json` para revisão. Dumps binários ficam locais até que um subconjunto relevante seja escolhido.

## Segurança de dados e interpretação
O arquivo de saída `output/raw/...bin` é uma cópia bruta de 8 MiB obtida por leituras `System Bus` no intervalo virtual `0x80000000–0x807FFFFF`, que é **hipótese de acesso KSEG0**, não domínio RDRAM validado. Para impedir conclusões precipitadas, o analisador exige quatro snapshots ON de duas épocas, metadados same-frame e tamanho exato. Compara valores float32 big e little endian nos offsets alinhados de 4 bytes, exigindo P1 estável, P2 estável e P1 diferente de P2. Saídas são apenas candidatos, com falsos positivos e negativos; posição pode exigir ponteiros, deslocamentos ou outra representação.

É essencial manter inimigos identificáveis, testar direção de deslocamento conhecida, observar ausência de movimento com Freeze, reproduzir noutra missão/sessão e distinguir câmera/Bond/animação. Não modificar `GoldenEye.mapping/catalog/symbols.json` ainda. Sem captura real, nenhum campo XYZ está identificado.

## Limitações técnicas
- O monitor detecta transições quando ambos os aliases concordam; não verifica se o **inimigo específico** está congelado.
- Capturas extensas podem ser lentas. Qualquer erro interrompe o script; arquivo incompleto não deve entrar na análise.
- Não reiniciar ROM ou carregar savestate durante a coleta. Frame discontinuities interrompem a sessão.
- O analisador inicial escolhe apenas as duas primeiras épocas ON completas.
