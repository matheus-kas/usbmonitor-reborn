# Protocolo da tela (Turing Smart Screen Rev A)

Documentação do protocolo serial usado pelo driver (`driver/turing_screen.py`).
Reimplementado a partir da especificação pública da comunidade
(turing-smart-screen-python, GPL-3.0) e validado no hardware `USB35INCHIPSV2`.

## Identificação

- A tela se apresenta como porta serial USB (CDC / COM virtual).
- Serial string: `USB35INCHIPSV2`. VID `0x1A86`, PID `0x5722` (chip WCH).
- O driver detecta a porta pelo serial string, com fallback para o par VID/PID.

## Conexão

- Serial a **115200 baud**, 8N1, controle de fluxo RTS/CTS.
- Observação: o chip trafega acima do baud nominal (USB full-speed), mas o firmware
  impõe um teto efetivo de ~128 KB/s (ver [Desempenho](#desempenho)).

## Comandos

Cada comando é um pacote de **6 bytes**, com o código do comando no último byte.

| Comando | Valor |
|---|---|
| RESET | 101 |
| CLEAR | 102 |
| SCREEN_OFF | 108 |
| SCREEN_ON | 109 |
| SET_BRIGHTNESS | 110 |
| SET_ORIENTATION | 121 |
| DISPLAY_BITMAP | 197 |

### Empacotamento de coordenadas

As coordenadas `x`, `y`, `ex`, `ey` (cantos do retângulo alvo) são empacotadas em bits
nos 5 primeiros bytes, cada uma com 10 bits:

```
byte[0] = x >> 2
byte[1] = ((x & 3) << 6) + (y >> 4)
byte[2] = ((y & 15) << 4) + (ex >> 6)
byte[3] = ((ex & 63) << 2) + (ey >> 8)
byte[4] = ey & 0xFF
byte[5] = comando
```

### SET_ORIENTATION

Pacote especial de 16 bytes. Bytes 0 a 5 iguais (com coordenadas zeradas e comando 121):

```
byte[6]  = orientacao + 100     # PORTRAIT=100, REVERSE_PORTRAIT=101,
                                #  LANDSCAPE=102, REVERSE_LANDSCAPE=103
byte[7]  = largura >> 8
byte[8]  = largura & 0xFF
byte[9]  = altura >> 8
byte[10] = altura & 0xFF
```

### SET_BRIGHTNESS

O nível vai no argumento `x`. Valor absoluto `255 - (percent/100)*255` (0 = mais claro,
255 = mais escuro).

## Envio de imagem (DISPLAY_BITMAP)

1. Envia o cabeçalho de 6 bytes com os cantos inclusivos: `(x0,y0)` e `(x1,y1)`.
2. Em seguida, os pixels crus, sem cabeçalho nem tamanho, em **RGB565 little-endian**,
   linha a linha (top-down, esquerda para direita).

Conversão por pixel:

```
valor = ((R >> 3) << 11) | ((G >> 2) << 5) | (B >> 3)
byte_baixo = valor & 0xFF        # enviado primeiro
byte_alto  = (valor >> 8) & 0xFF
```

Como o comando aceita um retângulo arbitrário, é possível atualizar **apenas uma região**
da tela, o que reduz proporcionalmente o tempo de envio.

## Desempenho

Medições no hardware real (banda efetiva ~128 KB/s):

| Área | Bytes/frame | Tempo/frame | FPS máx |
|---|---|---|---|
| 480x320 (cheia) | 307200 | ~2400 ms | 0,4 |
| 240x160 | 76800 | ~600 ms | 1,7 |
| 160x120 | 38400 | ~300 ms | 3,3 |
| 120x80 | 19200 | ~150 ms | 6,7 |

Conclusão: ideal para painéis de sensores a ~1 FPS. Vídeo fluido em tela cheia é inviável.

## Retenção de imagem

O comando CLEAR tende a deixar a tela clara, não preta, e conteúdo estático marca o painel
IPS (retenção de imagem). O driver oferece:

- `clear_black()`: preenche com preto de verdade (frame RGB565), evitando resíduos.
- `deghost()` e o recuperador do motor: alternam branco/preto/cores primárias para dissolver
  marcas fantasma.

## Status e pendências

- **Feito e validado no hardware:** detecção da porta, conexão, SCREEN_ON, brilho,
  orientação, envio de bitmap RGB565 em tela cheia, limpeza em preto, recuperação de retenção.
- **Medido:** teto de banda ~128 KB/s (tabela acima).
- **Usado:** pyserial sobre a porta COM virtual; conversão RGB565 em Pillow.
- **Pendente:** atualização parcial por região (dirty rectangles) para subir o FPS efetivo
  de painéis com pouco movimento; reconexão automática quando a porta cai; suporte a outras
  revisões de tela (Rev B, C, D).
