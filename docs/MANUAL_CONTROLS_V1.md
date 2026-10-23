# Manual Controls Detection v1 (BizHawk N64)

Esta etapa antecede Auto-Aim Mapping. Detecta nomes e valores reais reportados pelo BizHawk; não assume botões, eixos, layout ou endereços de RAM.

## Executar
No checkout atualizado do GoldenEye.assistant, abrir `manual_controls_v1.lua` pela Lua Console do BizHawk, usando a raiz do repositório como diretório atual. O script importa `lua/manual_controls_v1.lua`.

Capturar: sem entradas por alguns frames; cada botão isoladamente; analógico X/Y em ambas direções; pares de botões; mira e tiro; menus. Salvar cópia dos CSVs após cada sessão. Não rodar simultaneamente com script que injete comandos se a intenção for identificar entradas puramente manuais.

## CSVs
- `manual_controls_v1_samples.csv`: amostra **por controle, frame e fonte**. Campos: session,frame,phase,port,source,control,value,value_type
- `manual_controls_v1_events.csv`: mudança de controle; campos: session,frame,phase,port,source,control,event,old_value,new_value
- `manual_controls_v1_diagnostics.csv`: capacidades e falhas; campos: session,frame,phase,code,detail

Fontes tentadas: `joypad.getimmediate(1)` (entrada imediata do usuário), `joypad.get(1)` (entrada conforme API), `joypad.getwithmovie(1)` (incluindo movie). A disponibilidade e a semântica precisam ser validadas na versão/core em uso. Ausência é reportada; nenhuma substituição silenciosa.

O CSV de samples utiliza formato longo e grava todos os controles retornados, a cada frame, por padrão. Evitar sessões longas pela taxa de escrita. Os arquivos são gravados no diretório de trabalho do console Lua. Para configurar amostragem menos frequente altere `interval` no launcher.

**Garantias:** não escreve RAM, não chama `joypad.set`, não injeta controles, não ativa auto-shot. A etapa não interpreta ainda o significado dos controles no GoldenEye e não demonstra qual input o jogo efetivamente aplicou internamente. Os símbolos de memória permanecem no GoldenEye.mapping.
