# Arquitetura

O app é dividido em camadas independentes: driver da tela, sensores, modelo/renderização
de temas, motor de atualização e interface.

```
+---------------------------------------------------------------+
|                         ui/ (PySide6)                         |
|   main_window: preview, galeria, controles, bandeja           |
|   widgets: galeria de temas e miniaturas                      |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
|                      core/engine.py                           |
|  Loop em thread: le sensores -> renderiza -> envia pra tela    |
|  Controla brilho, orientacao, FPS e recuperacao de retencao   |
+----------+--------------------+----------------+--------------+
           |                    |                |
           v                    v                v
+------------------+  +------------------+  +------------------------+
| core/sensors.py  |  | core/renderer.py |  | driver/turing_screen.py|
| CPU, GPU, RAM,   |  | tema + leitura   |  | protocolo serial Rev A |
| disco, rede,     |  | -> imagem PIL    |  | (RGB565, comandos)     |
| uptime, relogio  |  +---------+--------+  +------------------------+
+------------------+            |
                               v
                     +--------------------+
                     | core/theme.py      |
                     | modelo de tema     |
                     | (JSON + widgets)   |
                     +--------------------+
```

## Fluxo de um quadro

1. `DisplayEngine._loop` (thread dedicada) chama `SensorHub.read()` e obtém um `Reading`.
2. `Renderer.render(reading)` desenha o tema atual numa imagem PIL de 480x320 (ou 320x480).
3. `TuringScreen.display_image(img)` converte para RGB565 e envia pela porta serial.
4. O mesmo quadro é emitido para a UI via callback `on_frame`, atualizando o preview.

A UI nunca escreve na porta diretamente: ela só ajusta parâmetros do motor (tema, brilho,
orientação, FPS, disco, adaptador). A escrita na serial fica serializada por um lock no motor,
inclusive durante a recuperação de retenção de imagem.

## Concorrência

- O loop de render roda em thread separada da UI.
- Um `threading.Lock` protege toda escrita na porta serial.
- A recuperação de retenção usa um `Event` que pausa o envio de sensores enquanto roda, e
  pode ser cancelada.

## Decisões de projeto

- **Temas em JSON** em vez do BinaryFormatter do app original: legível, editável e versionável.
- **Atualização a ~1 FPS** por causa do teto de banda da tela (ver PROTOCOLO.md).
- **Driver isolado** do resto: pode ser reutilizado por outros frontends ou scripts.

## Status e pendências

- **Feito:** driver, sensores, modelo/render de tema, motor em thread, UI com galeria e bandeja.
- **Usado:** Python 3.12, PySide6, Pillow, psutil, nvidia-ml-py, pyserial, winreg.
- **Em andamento:** editor visual de temas (base: `Renderer.widget_bbox`).
- **Pendente:** reconexão automática, perfis, testes automatizados e empacotamento como `.exe`.

Visão consolidada em `STATUS.md`; planejamento em `ROADMAP-SPRINTS.md`.
