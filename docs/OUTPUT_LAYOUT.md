# Organização de arquivos — GoldenEye.assistant

```text
GoldenEye.assistant/
├── main.lua                       # inicializador principal
├── analog_mapping_v1.lua          # inicializador BizHawk
├── manual_controls_v2_2_1.lua     # inicializador BizHawk
├── lua/                           # módulos fonte *.lua
├── config/                        # perfis/exportações Lua e configurações
├── tools/                         # scripts auxiliares *.py
├── docs/                          # documentação
├── tests/                         # testes
└── output/                         # artefatos gerados (ignorado no Git)
    ├── csv/                        # *.csv
    ├── sessions/                   # *_session.txt
    ├── commands/                   # filas *.cmd, subpastas por sessão
    ├── logs/                       # outros logs
    └── archive/                    # comandos legados *.txt
```

### Instalação ou migração
Encerre todos os observadores Lua antes de executar:

```powershell
git pull --ff-only origin main
python .\tools\prepare_output.py --migrate
```

`--migrate` transfere apenas os arquivos de resultados antigos conhecidos na raiz; não sobrescreve destinos existentes nem move módulos Lua. Os módulos ficam em `lua/`; inicializadores utilizados na Lua Console permanecem na raiz por compatibilidade.

### Execução
Abra os inicializadores na Lua Console, com diretório de trabalho na raiz do repositório. Execute a preparação uma vez antes da primeira captura. Os emissores de comandos já escrevem em `output/commands`.

Consultar relatórios:

```powershell
Import-Csv .\output\csv\manual_controls_v2_2_1_pending.csv | Format-Table
Get-Content .\output\csv\manual_controls_v2_2_1_validation.csv -Tail 10
Get-Content .\output\csv\analog_v1_samples.csv -Tail 20
```

A separação de saída foi aplicada aos observadores ativos `manual_controls_v2_2_1` e `analog_mapping_v1`. Detectores legados anteriores continuam usando suas rotas originais; para executar versões antigas, consulte a documentação específica. O catálogo canônico em `GoldenEye.mapping` não é alterado.
