# Auto-Aim Memory Discovery v1.1 — estabilidade e controle negativo

**Status:** implementado para teste local no BizHawk; ainda não validado com novas capturas. Não presume endereços de auto-aim e não altera RAM. O catálogo canônico permanece em [GoldenEye.mapping](https://github.com/marcosvilhena87/GoldenEye.mapping).

## O que mudou em relação à v1
- Seis capturas da **mesma sessão**, em vez de três: `A1`, `A_STABLE`, `B`, `B_STABLE`, `A2`, `CONTROL_A`.
- Arquivo de requisição **imutável e numerado** por captura, evitando `os.replace` e sua falha intermitente `WinError 5`.
- Coletor Lua grava em blocos de 4096 bytes diretamente no arquivo, evitando concatenar 8 MiB na memória Lua.
- Comparação rigorosa `A1 == A_STABLE == A2 == CONTROL_A != B == B_STABLE`.
- Cruzamento **opcional** com candidatos v1 por mesmo offset, somente se identidade da ROM, núcleo, domínio e tamanho forem compatíveis. Intersecção não prova causalidade.

## Início

No PowerShell, dentro de `GoldenEye.assistant`:
```powershell
git pull --ff-only origin main
python .\tools\prepare_output.py
```

Pare o coletor Lua anterior. No arquivo `autoaim_memory_discovery_v1_1.lua`, depois da conferência manual da ROM/núcleo e domínio, configure os valores *medidos* da sessão anterior **somente se a mesma API retornar estes valores agora**:
```lua
local DOMAIN = "RDRAM"
local EXPECTED_SIZE = 8388608
```
Esses valores estão **deliberadamente nulos** no repositório; não são suposições do código. Abra o novo script na Lua Console a partir da **raiz do repositório**. Verifique a mensagem `session=...`. A ausência de `RDRAM` em `memory.getmemorydomainlist()` não impede o acesso direto se `memory.getmemorydomainsize("RDRAM")` continuar confirmando o tamanho.

## Sequência experimental (um passo por vez)

| Rótulo | Estado manual exigido | Objetivo |
|---|---|---|
| A1 | Auto-aim ligado | Referência inicial |
| A_STABLE | Ligado, sem mudar configuração | Testar estabilidade ligado |
| B | Desligado | Contraste |
| B_STABLE | Desligado, sem mudar configuração | Testar estabilidade desligado |
| A2 | Religado | Reversibilidade |
| CONTROL_A | Ligado, abrir/fechar menu **sem mudar o auto-aim** | Controle negativo de interface |

Registre também se posição, arma, inimigos, tela e menu foram mantidos equivalentes. Em cada etapa, execute **apenas um comando**, confirme `captured LABEL` na Lua Console, verifique que o manifesto contém o rótulo e só então prepare a próxima condição:

```powershell
python .\tools\send_autoaim_mem_v1_1.py A1
python .\tools\send_autoaim_mem_v1_1.py A_STABLE
python .\tools\send_autoaim_mem_v1_1.py B
python .\tools\send_autoaim_mem_v1_1.py B_STABLE
python .\tools\send_autoaim_mem_v1_1.py A2
python .\tools\send_autoaim_mem_v1_1.py CONTROL_A
```

**Não execute todas as linhas de uma vez**. Cada snapshot lê 8.388.608 bytes via `memory.read_u8`, o que pode travar temporariamente a interface. A mensagem de envio não confirma captura. Se uma captura falhar, preserve os arquivos e inspecione a Lua Console; não reinicie nem pule rótulos. A v1 e a v1.1 usam manifestos e comandos separados, sem sobrescrever os 3 snapshots anteriores.

## Análise

```powershell
python .\tools\analyze_autoaim_mem_v1_1.py
```

Para intersecção opcional com a v1, após conferir identidade ROM/núcleo:
```powershell
python .\tools\analyze_autoaim_mem_v1_1.py --previous-v1-csv .\output\csv\autoaim_mem_v1_candidates_20261023T043912Z_38579.csv
```

Saída `output/csv/autoaim_mem_v1_1_candidates_<session>.csv`, com offsets de domínio `RDRAM` ainda classificados apenas como `candidate_control_filtered_only`. Os totais `stable_on`, `stable_off` e `negative_control_pass` contam bytes idênticos nos respectivos pares **sobre todo o domínio**, não apenas os alterados A1/B. `strict` indica candidatos após todos os filtros. `intersect_previous` mede sua presença na lista v1.

## Limitações e cautelas
- Testes de estabilidade entre capturas sucessivas não substituem testes de causalidade, endianness, largura ou reinicialização.
- A leitura é feita em bytes individuais por domínio, e offsets não se convertem automaticamente em endereços N64.
- Não atribuir `validated` a nenhum símbolo com base nestas correlações.
- Não publicar dumps da memória ou ROM no GitHub; guardar tudo em `output/` local.
- A identificação criptográfica da ROM e o núcleo N64 ainda precisam ser confirmados pelo operador.
