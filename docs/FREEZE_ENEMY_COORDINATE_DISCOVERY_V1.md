# Freeze All Enemies Alive — Enemy Coordinate Discovery v1

## Objetivo
Identificar campos de posição **dos inimigos** (não apenas Bond, câmera, velocidade, animação ou IA) por contrastes de Freeze OFF/ON/OFF. Nenhuma coordenada é considerada validada por este documento.

## Fonte externa e ressalva
Cheat GameShark histórico: `8002C90C 00FF` ("Freeze All Enemies Alive"). Referências:
- https://codetwink.com/view-cheats-1686-title-all%2Blevel%2Bcodes-page-13.html
- https://almarsguides.com/retro/walkthroughs/n64/games/goldeneye007/gameshark/singleplayercodes/alllevelcodes/

O prefixo 80 descreve uma escrita de byte para um endereço N64 na convenção GameShark; **não** demonstra endereço/semântica de XYZ na API RDRAM do BizHawk. Verificar ROM e tradução física de endereços antes de relacionar qualquer observação. Desativar o cheat pode não restaurar o byte original nem reverter um estado de jogo já alterado. Não aplicar escritas Lua adicionais.

## Pré-requisitos
- ROM/variante, SHA-256, núcleo N64, BizHawk, missão, dificuldade, slot, save state e configurações dos cheats registrados.
- Conferir a dimensão real e o domínio da memória via API; distinguir offsets de RDRAM de endereços virtuais N64.
- Salvar savestate BASE com ao menos 1 inimigo visível e nenhum input, antes do cheat. Preservar uma cópia.
- Deixar o script de captura em modo apenas-leitura; a ativação do GameShark é manual no emulador.
- Registrar frame preciso de cada transição, visibilidade, trajetória e ação do inimigo. Não afirmar congelamento apenas porque parou de andar.

## Matriz de sessões — repetir pelo menos 3 vezes
Partir **sempre** do mesmo BASE, com uma sessão inteira sem cheat como controle.
1. BASE/OFF: 120 frames parado; registrar movimento natural e IA.
2. OFF/MOVE: 120 frames, induzir inimigo a andar mantendo Bond imóvel; anotar percurso visual.
3. ON/SETTLE: ativar o cheat; anotar frame; descartar transiente de 30 frames.
4. ON/HOLD: 120 frames sem movimentar Bond; verificar se inimigo, animação, mira, tiros e física se mantêm.
5. ON/BOND_MOVE: 120 frames movendo Bond; registrar o deslocamento físico de Bond e posição visual do inimigo.
6. ON/ROTATE: girar Bond sem transladar; verificar posição mundial vs coordenadas de câmera.
7. OFF/RESUME: desativar cheat; observar por 120 frames. Se não voltar, reiniciar do BASE para OFF em vez de atribuir causalidade.
8. Novo inimigo, outro local e outra missão; repetir. Controles negativos: câmera girando sem deslocamento e inimigo ausente.

## Captura de memória
Primeira execução: **não** ler uma janela de endereços como XYZ confirmado. Priorizar snapshot binário dos bytes RDRAM em momentos de marcação, preservando bytes originais, frame e fase. Para instantâneos grandes, pausar no ponto escolhido e usar dump do emulador; nunca correlacionar leituras capturadas durante muitos frames como se fossem instantâneos atômicos. Referenciar explicitamente a convenção de endereço do dump.

Para triagem exploratória, comparar word-aligned/unaligned u16/u32 e float32 nas duas endianidades sobre bytes crus, descartando NaN/Inf e valores sem consistência temporal. Não confundir endereços virtuais da ROM/GS com offsets de dump da RDRAM. Não restringir a pesquisa às janelas de Bond já usadas nas séries v2-v3.

CSV de eventos: `session,frame,phase,cheat_reported,player_motion,enemy_visual_motion,enemy_count_visible,notes`. Campos desconhecidos ficam vazios, sem inferência.

## Análise e critérios de evidência
1. Diferença OFF-moving -> ON-held: detectar regiões com variação do estado de movimento e campos que estabilizam. Mudanças são **candidatos**, não prova de posição.
2. Separar ON-held versus ON-BOND_MOVE/ROTATE: coordenadas absolutas do inimigo deveriam resistir a movimento/rotação de Bond, enquanto medidas relativas ou câmera podem variar.
3. Repetir OFF-resume e comparar a um OFF-only contrafactual do mesmo BASE. Considerar efeitos colaterais do freeze e do savestate.
4. Exigir no mínimo dois inimigos com trajetórias independentes e repetição em >=3 sessões; correlacionar com deslocamentos e direções **observados externamente**.
5. Inferir estrutura: offsets vizinhos com três campos coerentes, deslocamento consistente entre instâncias, vida útil de ponteiro, identidade por inimigo e disponibilidade após spawn/despawn.
6. Teste físico: inimigo anda em duas direções independentes, retorno aproximado, câmera girando, Bond movendo e freeze ON/OFF. Verificar continuidade, direção e escala.
7. Somente promover a `GoldenEye.mapping` com ROM/núcleo confirmados, tipo, endianidade, domínio, ponteiro/offset ou resolução, condições de validade, controles positivos/negativos e arquivos brutos.
8. Documentar rejeitados e ambiguidades. `candidate` -> `observed` -> `reproduced` -> `validated` conforme `GoldenEye.mapping/docs/methodology.md`.

## Relação com investigações anteriores
Consultar `SPATIAL_AXIS_AWARE_POSITION_DISCOVERY_V3_7.md`, `SPATIAL_PHYSICAL_FAILURE_DIAGNOSIS_V3_6.md`, `DUAL_U8_RDRAM_PROBE_0D36F4_0D3720_V1.md`. Não reinterpretar candidatos de movimento de Bond como coordenadas de inimigos. A distinção entre endereço em `0x0D....` e o tamanho observado de RDRAM deve ser explicitamente resolvida, não ignorada.

## Critérios de sucesso
Entregar: capturas OFF-only/ON/OFF, tabela de comportamento visual e temporal, shortlist com valores crus, controle negativo, instâncias múltiplas e um relatório com evidências de identidade do inimigo. Resultado negativo ("freeze modifica animação, não translada" / "não restaurou ao desativar" / "janela não cobre inimigo") também é válido.
