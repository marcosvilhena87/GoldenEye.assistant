# Arquitetura v0.1

`main.lua` centraliza o bootstrap. Módulos Lua não descobrem endereços nem possuem offsets embutidos.

`GoldenEye.mapping` é a fonte canônica. `tools/export_mapping.py` produz um snapshot Lua local para um `rom_id`, usando apenas entradas compatíveis. O exportador nunca promove estados de confiança.

O adaptador de emulador será implementado após identificar versão, núcleo N64 e APIs disponíveis. Por padrão, a memória usa adaptador `nil` e o controle não envia botões.

## Invariantes
1. O catálogo não identifica automaticamente a ROM em execução. Antes de ativar leitura, implementar verificação independente da ROM carregada (hash ou identidade comprovadamente equivalente).
2. Validar o contexto completo antes de qualquer acesso: domínio, largura, endianidade, resolução e condições; metadados completos **não significam acesso seguro por si só**.
3. Em modo normal, aceitar somente `validated`. Modo experimental exige habilitação explícita e ainda não concede acesso ao adaptador por padrão.
4. Qualquer ausência, inconsistência ou ambiguidade bloqueia a ação.
5. Auto-aim, elegibilidade do alvo, estado da arma, cadência e autorização de disparo são comportamentos separados.
6. Manter evidência e commit do mapping para reprodutibilidade.

## Próximos incrementos
- Verificador da identidade da ROM no runtime.
- Adaptador BizHawk específico ao core validado.
- API de estado do jogador/inimigos, com símbolos comprovados.
- Monitor observacional para auto-aim; somente após validação, avaliação do auto-shot.
