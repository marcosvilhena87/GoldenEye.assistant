# Auto-Align Roadmap v1 — giro de Bond orientado pelo Auto-Aim

Data: 2026-10-23. Estado: **projeto**, não funcionalidade ativa.

## Propósito
Usar a correção horizontal do auto-aim **após validação experimental** como referência para girar Bond na direção do alvo, sem substituir nem presumir a semântica da assistência de mira nativa.

Fonte canônica: [GoldenEye.mapping — hipóteses e protocolo](https://github.com/marcosvilhena87/GoldenEye.mapping/blob/main/docs/AUTOAIM_HORIZONTAL_AUTOALIGN_V1.md).

## Etapas com portas de validação
1. **Auto-Aim Memory Discovery v1.2:** concluir a validação de candidatos, controles e identidade da ROM.
2. **Horizontal Correction v1:** demonstrar medição confiável de correção horizontal, direção do sinal, escala e validade com/sem alvo.
3. **Bond Heading Discovery v1:** determinar orientação horizontal de Bond em testes de giro manual.
4. **Turn Controller Calibration v1:** medir resposta do eixo/botões do BizHawk para giro, latência e saturação. Não assumir a correspondência entre sinal da arma e sinal do joystick.
5. **Auto-Align v1:** controlador conservador com zona morta, ganho limitado, limite por frame e parada quando o alvo/símbolo perder validade.
6. **Auto-Align v2:** acompanhar alvo em movimento; tratar mudanças de alvo, oclusão, histerese e oscilações.
7. **Auto-Shot:** integração posterior e opcional, com disparo desabilitado por padrão.

## Fluxo lógico proposto
```text
GoldenEye.mapping (símbolos validados da ROM exata)
    -> leitura segura do auto-aim e heading
    -> validade/identidade do alvo
    -> estimativa de erro horizontal calibrada
    -> controle de giro limitado
    -> botão/eixo no BizHawk
```

Relação de controle hipotética: `u = clamp(Kp * erro, -u_max, u_max)`, com zona morta, watchdog e sinal determinado em calibração. **O desvio da arma não é necessariamente o ângulo necessário para girar Bond.**

## Segurança operacional e testes
- Começar com observador read-only e logs; depois simulação sem comandos; por fim giro em cenário controlado **sem tiro**.
- Desarmado ao iniciar; ativação explícita pelo operador, tecla de desligamento, timeout, limitação de rotação e parada segura.
- Se o símbolo não estiver `validated`, ROM não corresponder, alvo ficar ambíguo ou frame falhar, **não enviar entrada**.
- Não escrever na RAM e não misturar controles manuais com comandos automáticos sem arbitragem explícita.
- Testar esquerda/centro/direita, distâncias, posições atrás de Bond, alvos múltiplos, obstáculos, mudanças rápidas, sem alvo, armas e dificuldades.
- Logar frame, identificação da ROM, símbolos/versão do catálogo, leitura bruta, erro, sinal de controle, comando aplicado e motivo de desarme.
- Nenhum `autoalign.lua` executável deve ser ligado ao `main.lua` antes desses gates.

## Interfaces futuras (não implementadas)
```lua
local state = AutoAim.read()  -- somente símbolos validados
local heading = BondHeading.read()
local control = AutoAlign.step(state, heading)
-- Controller.apply(control) só com habilitação explícita e validade integral
```

A API acima é ilustrativa, não define campos de RAM nem afirma disponibilidade das funções.
