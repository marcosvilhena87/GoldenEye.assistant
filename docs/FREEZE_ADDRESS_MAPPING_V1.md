# Freeze Address Mapping v1

## Origem
Usuário observou no **RAM Watch** do BizHawk 2.11.1: `02C90C d u 0 RDRAM` com Freeze All Enemies Alive desligado e `255` ligado. Inimigo fica imóvel com ON e retoma sua trajetória quando OFF. Ao mesmo tempo a API Lua reportou somente ROM, registradores, EEPROM, SRAM, FlashRAM, System Bus e CPU registers — sem RDRAM. A leitura Lua `memory.read_u8(0x02C90C, "System Bus")` retornou 255 mesmo com o cheat OFF. Isso **não** prova que `0x02C90C` do barramento acessa o byte do RAM Watch.

## Objetivo
Investigar correspondência entre offset RDRAM do RAM Watch e leitura do `System Bus`, sem escrita e sem pressupor alias correto. Testar offset físico direto, KSEG0 e KSEG1 como hipóteses da arquitetura N64; o comportamento exato depende do núcleo e tradução da API. O byte observado é candidato a **indicador de estado**, nunca coordenada XYZ.

## Passos
1. `python tools/prepare_output.py` (ou criar `output/csv`, `output/sessions`, `output/commands`).
2. Abra GoldenEye no BizHawk, verifique cheats e RAM Watch. Em Tools > Lua Console abra `freeze_address_mapping_v1.lua`. Leia `session` na saída.
3. **Antes** de cada marcador, coloque o cheat no estado correspondente; espere alguns frames, confira no RAM Watch (OFF=0 ou ON=255) e registre o valor observado manualmente. Mantenha cada fase por >=120 frames.
4. No PowerShell, um comando por fase, esperando o `marked` do Lua: `python tools/send_freeze_address_v1.py OFF1`, depois `ON1`, `OFF2`, `ON2`, `STOP`. NÃO mandar todos de uma vez.
5. Arquivos: `output/csv/freeze_address_v1_<session>_timeline.csv` e `_markers.csv`.
6. `python tools/analyze_freeze_address_v1.py output/csv/freeze_address_v1_<session>_timeline.csv`. Preferir `--output output/...json` para guardar o resultado.

## Interpretação
`0x002C90C` (mesmo offset), `0x802C90C` (KSEG0) e `0xA02C90C` (KSEG1) são candidatos de barramento, não aliases confirmados. **Os endereços efetivos no script usam 0x002C90C, 0x802C90C e 0xA02C90C (formatados em 8 dígitos).** Se todos retornarem 255 mesmo no OFF, nenhum será aceito. O script realiza três leituras por frame e usa apenas leitura; capturar temporalmente sob a mesma ROM e core. Descartar resultados de endereços não mapeados, erros de leitura e discrepâncias com RAM Watch. Leituras que correspondam em todos os estados são apenas candidatos; repetir em sessão independente e com controle negativo antes de inserir símbolo validado em GoldenEye.mapping.

## Limites
Estado do RAM Watch confirmado pelo operador, ainda sem identidade da ROM/núcleo/valores raw anexos. O comparador exige correspondência OFF=0 e ON=255 em todas as amostras da fase, e pode rejeitar candidatos reais durante transientes; aguardar estabilização. Nenhum arquivo canônico é alterado nesta versão.
