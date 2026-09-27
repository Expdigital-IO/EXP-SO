# EXP Brand Motion — Motion System

Vídeos de apresentação da marca **exp digital** feitos 100% em código.
Zero After Effects: HTML + trilha composta em numpy + render Playwright/ffmpeg.

| # | Vídeo | Arquivo | Formato |
|---|---|---|---|
| 001 | UI Morph Reel (`index.html`) | `exp-brand-motion.mp4` | 1080×1920 · 60fps · 14s · loop |
| 002 | Logo Flash Reel (`logo-reel.html`) | `exp-logo-reel.mp4` | 1080×1920 · 60fps · 10s · loop |
| 003 | Logo Sting (`logo-sting.html`) | `exp-logo-sting.mp4` | 1080×1920 · 60fps · 3.6s · loop |
| 004 | Ident (`logo-ident.html`) | `exp-logo-ident.mp4` | 1080×1920 · 60fps · 5s · loop — cinema dive/blast, render com `RENDER_SUB=10` |
| 005 | Brand Film (`brand-film.html`) | `exp-brand-film.mp4` | 1080×1920 · 60fps · 16s · loop — 3 atos, trilha `film-audio.py`, render com `RENDER_SUB=10` |

## 005 — Brand Film

Apresentação completa da marca em 16 s (8 compassos a 120 BPM), em três atos:

| Tempo | Ato | Cenas |
|---|---|---|
| 0–4,75 s | **I · Branding** | símbolo neon → positivo → sobre cor · capítulo 01 *"Criativo também é estratégia."* · paleta com proporção de uso (60/25/10/5) · espécime tipográfico Geist (4 pesos) · billboard · papelaria |
| 4,75–6,25 s | ponte | perfil do Instagram → **mergulho de câmera no avatar** → iPhone nasce do card laranja |
| 6,25–12 s | **II · Marketing** | capítulo 02 *"Do zero à operação digital."* · dashboard de campanhas (receita, ROAS, leads, CTR) · funil de performance · anúncio patrocinado + notificações de lead/venda · busca com a EXP em 1º · marquee |
| 12–16 s | **III · Assinatura** | blast selando a tela → macro metálico · manifesto *"Você traz o negócio. A EXP traz a estrutura."* · endcard com CTA |

Os números dos mockups são ilustrativos.

**Trilha (`film-audio.py`):** corporate house em Lá menor. Piano elétrico FM
com acordes sincopados (Am9 → Fmaj9 → Cmaj9 → G6/9), baixo no contratempo,
hats com swing, reverb por convolução. O arpejo entra no Ato II, a caixa
acelera no build, há ~60 ms de silêncio no frame laranja sólido antes do boom,
acordes em meio-tempo no manifesto e cadência E7 → Am9 no endcard.

```bash
python3 film-audio.py                                          # → /tmp/exp-film.wav
RENDER_SUB=10 python3 render.py /tmp/film.mp4 brand-film.html 16
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
$FF -i /tmp/film.mp4 -i /tmp/exp-film.wav -c:v copy -c:a aac -b:a 192k -shortest exp-brand-film.mp4
```

## 002 — Logo Flash Reel

Montagem de identidade no estilo *brand reveal*: cortes secos no grid de
120 BPM, cada cena mostra o **logo oficial** (máscaras extraídas dos
arquivos da marca em `assets/`) numa aplicação diferente — blueprint de
construção do símbolo, ondas concêntricas, cortes sobre branco, versão
sobre cor, lockup horizontal, perfil do Instagram, card da App Store,
blueprint da tipografia, totem OOH, site, fitas diagonais, cor secundária
(pêssego), macro e lockup final. 14 cenas em ritmo de referência (0,25–0,75s por corte), blast selando a tela para a virada, um hit de som em cada
corte (`logo-audio.py`).

# 001 — UI Morph Reel

**Formato:** Reels 1080×1920 · 60 fps · 14 s · loop perfeito · 120 BPM · 7 compassos

## O conceito

Um único elemento — nunca há corte. O mesmo shape se transforma em cada
estado de UI mudando tamanho, raio e cor, enquanto o conteúdo troca com um
blur curto. Um cursor real dirige cada mudança com cliques e drags de
verdade. A câmera dá zoom para cada estado preencher o frame. O último
frame é idêntico ao primeiro, então o vídeo loopa sem costura.

### A narrativa no grid de batidas (algo acontece em todo beat)

| Beat | Estado |
|---|---|
| 0 | CTA **CONHEÇA A EXP** (laranja, o botão real da marca) |
| 1 | clique → vira **loader** |
| 3 | loader fecha → **check** (pop) |
| 4 | check → **dynamic island** `exp®` |
| 5–9 | **player** "Brand Anthem — exp® digital" · play/pause morph · scrub real da barra |
| 10–11 | player → **slider de volume** · drag além do máximo estica o pill (rubber band) |
| 13 | **toggle** flipa no beat (knob com molas de duas bordas) |
| 14–15 | knob vira **indicador líquido de tabs**: Design · Tecnologia · Estratégia |
| 16–19 | tabs abrem em **gráfico** que se desenha (+248%) com tooltip no hover |
| 20–23 | colapsa em **⌘K** · digita "la" · filtra · Enter em "Lançar projeto" |
| 24–25 | **toast** "Projeto lançado" |
| 26–27 | toast morfa de volta ao CTA · cursor volta ao início → **loop** |

## Identidade

- Canvas preto quente `#0B0908`, cards dark `#1B1714`, texto `#F4F1EE`/`#9A938C`
- Acento único: **laranja EXP** `#FF4E10`
- Tipografia: **Geist** (única família, 4 pesos)
- HUD replica o layout dos criativos: `exp digital` (topo esq.),
  `HUB DE SERVIÇOS DIGITAIS` (topo dir.), `DESIGN. TECNOLOGIA. ESTRATÉGIA.`
  (rodapé esq.), `expdigital.io` (rodapé dir.)

## Engenharia

- `index.html` — toda a animação é uma função pura do tempo dentro de
  `seek(t)`: sem transições CSS, sem timers, sem estado entre frames.
  Springs são respostas ao degrau em forma fechada; um valor que muda de
  alvo várias vezes é a soma de uma mola por mudança. Drags são manipulação
  direta (o valor vem da posição do cursor enquanto pressionado; no release
  entra uma mola livre a partir da posição e velocidade do soltar).
  Abrir o arquivo no navegador dá o preview em tempo real.
- `audio.py` — trilha 120 BPM composta em numpy (royalty-free por
  construção), começa no downbeat, cada som de UI colocado no tempo exato
  do evento, validação do grid de batidas por detecção de onsets.
- `render.py` — 4 subframes por frame a 240 fps virtuais, blended com
  `ffmpeg tmix` para motion blur, encode x264 CRF 16.
- `beatsheet.py` — um frame por beat como contact sheet, para revisar o
  grid antes do render completo.

## Como renderizar

```bash
pip install numpy playwright imageio-ffmpeg pillow
python3 audio.py                       # → /tmp/exp-anthem.wav
python3 render.py /tmp/exp-mute.mp4    # → vídeo sem áudio
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
$FF -i /tmp/exp-mute.mp4 -i /tmp/exp-anthem.wav -c:v copy -c:a aac -b:a 192k -shortest exp-brand-motion.mp4
```

As fontes Geist (SIL OFL, ver `fonts/OFL-LICENSE.txt`) são servidas
localmente — nenhuma dependência externa no render.
