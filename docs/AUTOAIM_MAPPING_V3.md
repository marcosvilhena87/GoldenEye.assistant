# Auto-Aim Mapping v3 — Epochs, intervenções e contraste A/B/A

Experimento **somente leitura**. Sem endereços, ponteiros, automação de tiro ou alterações na memória. O `GoldenEye.mapping` continua sendo a única fonte canônica para símbolos de memória, e o leitor de auto-aim permanece `unresolved`.

## Evolução da v2

- Os eventos possuem `session` e `epoch`. Se o frame atual for menor que o anterior, a época aumenta e surge `FRAME_REGRESSION`. Isso não identifica a causa (pode ser save state, rewind etc.).
- Eventos de botões brutos `RAW_R` e `RAW_Z` separados; os rótulos obtidos da API são **provisórios**, não comprovam uma ação visual, e sua ausência não prova que um botão físico não foi pressionado.
- `INTERVENTION` informa intervenções do operador (ex.: `manual_aim_R`, `fire_Z`, `savestate_loaded`, `autoaim_enabled_in_menu`). `EVENT` informa **observações**, nunca fatos automáticos.
- O relatório agrupa por sessão, época e fase e não mistura retrocessos de tempo com repetições independentes.

## Execução

Pare a v2. Na raiz do repositório:

```powershell
git pull --ff-only origin main
python .\tools\prepare_output.py
```

No BizHawk, abra `autoaim_mapping_v3.lua`. Confirme `output/sessions/autoaim_v3_session.txt`.

## A/B/A

Prepare o mesmo cenário e arma com alvo isolado, de preferência usando savestate. Marque intervenções separadamente e observe **sem pressionar R** para os contrastes automáticos. Cada comando abaixo deve ser executado em seu momento, não em lote:

```powershell
python .\tools\send_autoaim_v3.py PHASE aba_enabled_1
python .\tools\send_autoaim_v3.py INTERVENTION autoaim_enabled_in_menu
python .\tools\send_autoaim_v3.py EVENT aim_shift_observed
python .\tools\send_autoaim_v3.py PHASE aba_disabled
python .\tools\send_autoaim_v3.py INTERVENTION autoaim_disabled_in_menu
python .\tools\send_autoaim_v3.py EVENT no_aim_shift_observed
python .\tools\send_autoaim_v3.py PHASE aba_enabled_2
python .\tools\send_autoaim_v3.py INTERVENTION autoaim_enabled_in_menu
python .\tools\send_autoaim_v3.py EVENT aim_shift_observed
```

**Atenção:** os exemplos de `EVENT` só devem ser enviados se a observação realmente ocorrer, e as opções `INTERVENTION` somente após a ação ter ocorrido no jogo. No caso de savestate, anote `INTERVENTION savestate_loaded` depois de carregá-lo. Se houver regressão de frames, o logger iniciará outra `epoch`.

## Consulta

```powershell
Get-Content .\output\csv\autoaim_v3_diagnostics.csv -Tail 20
Get-Content .\output\csv\autoaim_v3_events.csv -Tail 30
python .\tools\report_autoaim_v3.py
```

O relatório apresenta fases, épocas, resultado do operador e quantidade de transições detectadas para R/Z. `RAW_R` não equivale necessariamente à mira manual; `RAW_Z` não comprova disparo efetivo.

## Limites e próximos passos

O experimento observa anotações humanas; não mede coordenadas ou ângulos. Não há mecanismo validado em RAM. Antes de promover evidências no mapping, repetir em condições controladas e registrar ROM, core N64, versões, controles negativos e diferenças observáveis. Não se deve afirmar `validated` apenas porque houve A/B/A.
