# Status do projeto

Visão geral do que já foi feito, das tecnologias usadas e do que falta.
Atualizado em 2026-11-25.

## O que fizemos

- Engenharia reversa do app original do fornecedor (ver `ANALISE-APP-ORIGINAL.md`).
- Identificação do hardware: tela Turing Smart Screen Rev A (`USB35INCHIPSV2`, VID 1A86 / PID 5722).
- Driver serial próprio, validado na tela real (RGB565, 115200 baud).
- Coleta de sensores: CPU, GPU NVIDIA (NVML), RAM, disco, rede por adaptador, uptime, relógio.
- Modelo de tema em JSON editável, renderizador e motor de atualização em thread.
- 8 temas, sendo 3 recriados das artes originais do fornecedor (Gradient, MagicBlue, NZXT).
- Interface PySide6: preview ao vivo, galeria visual de temas, controles de brilho,
  orientação, FPS, disco e adaptador de rede, bandeja do sistema e iniciar com o Windows.
- Recuperador de retenção de imagem (dissolve marcas fantasma no painel).
- Correção de ghosting (limpeza em preto real ao conectar/sair).
- Medição do desempenho da tela (teto de banda ~128 KB/s).
- Documentação completa, README profissional e licença GPL-3.0.
- Base do editor de temas: cálculo da área de cada widget (`Renderer.widget_bbox`).

## O que usamos

| Área | Tecnologia / ferramenta |
|---|---|
| Linguagem | Python 3.12 |
| Interface | PySide6 (Qt) |
| Renderização | Pillow (PIL) |
| Sensores | psutil, nvidia-ml-py (NVML) |
| Comunicação | pyserial (porta COM virtual) |
| Iniciar com Windows | winreg (registro HKCU\\...\\Run) |
| Engenharia reversa | REA (análise do `UsbMonitor.exe` .NET) |
| Referência de protocolo | turing-smart-screen-python (comunidade, GPL-3.0) |
| App original analisado | C# / .NET Framework 4.0, WinForms, GDI+ |

## Pendências

Detalhamento e ordem em `ROADMAP-SPRINTS.md`.

- **Editor visual de temas** (prioridade): arrastar widgets, escolher imagem/cor de fundo,
  editar propriedades, criar dashboards, remover unidade duplicada do "%".
- Corrigir temas do fornecedor com texto já presente na arte (ex: "%").
- Recriar o restante dos temas do fornecedor (~35, imagens já extraídas).
- Temperatura e fan de CPU via LibreHardwareMonitor.
- Tema Claude Code (mascote + uso/limites).
- Widget de clima e novos tipos de widget (gráfico, ícone).
- Reconexão automática da tela e perfis (tema + brilho + orientação).
- Empacotar como executável único (PyInstaller) e publicar no GitHub.
- Substituir o `LICENSE` pelo texto oficial completo da GPL-3.0 antes de publicar.

## Backlog

- Player de vídeo/GIF em janela pequena (limitado a ~3 FPS pela banda da tela).
- Suporte a outras revisões de tela (Rev B, C, D).
- Integração com AIDA64 (memória compartilhada), como o app original.
