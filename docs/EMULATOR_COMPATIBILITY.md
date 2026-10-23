# Emulator Compatibility — identificação inicial

## Executável analisado (22/10/2026)
- Produto: EmuHawk / BizHawk.
- Versão: **2.11.1** — identificada pela correspondência exata do SHA-256 com metadados publicados de EmuHawk 2.11.1.
- Arquivo: `EmuHawk.exe` (usuário forneceu como `EmuHawk(1).exe`).
- Tamanho: **5.376.512 bytes**.
- SHA-256: `f8cdb93551a544f680bf3876d9d8d72643859e7a44a23b04e1a25b92e48f80cd`.
- Tipo detectado: PE32 executável .NET, GUI Windows.
- Referências binárias: N64, GLideN64 e Angrylion.
- Referência externa de identificação: https://defkey.com/exe/5869

## Limites dessa identificação
Este arquivo isolado **não** prova o núcleo N64 ativo, disponibilidade das DLLs, configurações da instância, domínios de memória disponíveis ou compatibilidade com o runtime instalado. Não executar o arquivo para inferir esses detalhes.

## Próxima verificação no computador do usuário
1. Abrir a ROM GoldenEye USA rev0 na instalação completa do BizHawk.
2. Registrar **Help > About**, informações do core e configuração N64.
3. No console Lua do BizHawk, consultar nomes dos domínios acessíveis (sem ler endereços):
   ```lua
   for _, name in ipairs(memory.getmemorydomainlist()) do
     print(name)
   end
   ```
4. Registrar nomes/dimensões dos domínios e APIs efetivamente disponíveis. Não inferir deslocamentos.
5. Somente depois implementar um adaptador dedicado ao núcleo constatado, sempre sob confirmação de ROM e consulta ao GoldenEye.mapping.

## Política
Nenhuma operação de escrita, injeção de botões ou auto-shot habilitada até validação do contexto, símbolos e comportamentos.
