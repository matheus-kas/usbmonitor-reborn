# Formato de tema

Temas são arquivos JSON em `themes/`, carregados pelo `core/theme.py`. Cada tema define
o tamanho, o fundo e uma lista de widgets desenhados por cima.

## Estrutura do tema

| Campo | Tipo | Descrição |
|---|---|---|
| `name` | texto | Nome exibido na galeria e no arquivo. |
| `width`, `height` | inteiro | 480x320 (paisagem) ou 320x480 (retrato). |
| `background_color` | hex | Cor de fundo sólida (ex: `#0C0E1C`). |
| `background_image` | caminho ou null | Imagem de fundo. Caminho relativo à raiz do projeto. Transparência é composta sobre `background_color`. |
| `widgets` | lista | Widgets desenhados na ordem da lista. |

## Widgets

Campos comuns: `type`, `x`, `y`, `field`, `label`, `unit`, `fmt`, `font`, `size`, `bold`,
`color`, `align`.

| `type` | O que faz | Campos relevantes |
|---|---|---|
| `text` | Valor de um sensor como texto. | `field`, `label`, `unit`, `fmt`, `align` |
| `label` | Texto fixo. | `label` |
| `clock` | Igual a `text`, para relógio/data. | `field` (`clock`/`date`) |
| `bar` | Barra de progresso horizontal. | `field`, `width`, `height`, `min_value`, `max_value`, `bg_color`, `fill_color` |
| `ring` | Arco/anel de progresso. | `field`, `width` (diâmetro), `height` (espessura), `bg_color`, `fill_color` |

- `align`: `left` (padrão), `center` ou `right`. Útil para centralizar valores dentro de
  anéis ou cards.
- `fmt`: formato Python para números (ex: `"{:.0f}"`, `"{:.1f}"`).
- `unit`: sufixo anexado ao valor (ex: `"%"`, `" KB/s"`, `"C"`).

## Campos de sensor

| Campo | Descrição |
|---|---|
| `cpu_percent` | Uso de CPU (%). |
| `cpu_freq_mhz` | Frequência de CPU (MHz). |
| `cpu_temp_c` | Temperatura de CPU (°C, quando disponível). |
| `ram_percent` | Uso de RAM (%). |
| `ram_used_gb`, `ram_total_gb` | RAM usada/total (GB). |
| `gpu_name` | Nome da GPU. |
| `gpu_percent` | Uso da GPU (%). |
| `gpu_temp_c` | Temperatura da GPU (°C). |
| `gpu_mem_percent` | Uso da VRAM (%). |
| `gpu_fan_percent` | Rotação do fan da GPU (%). |
| `disk_percent` | Uso do disco selecionado (%). |
| `disk_used_gb`, `disk_total_gb` | Disco usado/total (GB). |
| `net_up_kbps`, `net_down_kbps` | Upload/download do adaptador (KB/s). |
| `net_adapter` | Nome do adaptador monitorado. |
| `uptime` | Tempo ligado formatado (`2d 05:12:30`). |
| `clock` | Hora atual (`HH:MM:SS`). |
| `date` | Data atual (`dd/mm/aaaa`). |

## Exemplo

```json
{
  "name": "Meu Painel",
  "width": 480,
  "height": 320,
  "background_color": "#0C0E1C",
  "background_image": null,
  "widgets": [
    { "type": "clock", "x": 20, "y": 12, "field": "clock", "size": 44, "bold": true, "color": "#00E6FF" },
    { "type": "label", "x": 20, "y": 90, "label": "CPU", "size": 18, "bold": true, "color": "#FFFFFF" },
    { "type": "text",  "x": 180, "y": 90, "field": "cpu_percent", "unit": "%", "size": 18, "color": "#00C8FF" },
    { "type": "bar",   "x": 240, "y": 92, "field": "cpu_percent", "width": 210, "height": 14, "fill_color": "#00C8FF" }
  ]
}
```

## Criar e aplicar

- Edite ou copie um JSON em `themes/` e ele aparece na galeria ao reabrir, ou use
  **Importar tema** na interface.
- Os temas prontos são gerados por `gerar_temas.py` a partir de `core/theme_presets.py`.

## Status e pendências

- **Feito:** modelo JSON, 5 tipos de widget (text, label, clock, bar, ring), alinhamento,
  imagem de fundo com transparência, 8 temas prontos.
- **Usado:** Pillow para render; fontes do Windows (Segoe UI, Arial, Consolas).
- **Pendente:** editor visual (arrastar/editar sem mexer no JSON), escolher imagem de fundo
  pela interface, remover unidade quando a arte já traz o texto, novos tipos de widget
  (gráfico de linha, ícone), recriar o restante dos temas do fornecedor.
