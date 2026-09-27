# EXP Brand Film — quadros para edição

Cada arquivo é o **quadro-chave de uma cena** do filme de 16 s: o instante em
que a composição está completa. O movimento continua na animação; você edita
o *layout final* e eu reconstruo a animação em cima dele.

## O que tem aqui

| Arquivo | Para quê |
|---|---|
| `01_…png` a `20_…png` | uma cena por arquivo, 1080×1920 (Photoshop, Figma, Canva, celular) |
| `brand-film-cenas.pdf` | as 20 cenas em páginas vetoriais: **os textos continuam editáveis** |
| `guia.png` | visão geral com número e segundo de cada cena |

## No Canva (recomendado)

Pasta **EXP Brand Film — Quadros para edição** (https://www.canva.com/folder/FAHWbb6rgUU):

| Design | ID | Uso |
|---|---|---|
| ★ EXP Brand Film — EDITAR AQUI (20 cenas) | `DAHWbVB9dU0` | edite aqui: uma página por cena |
| EXP Brand Film — REFERÊNCIA (visual original) | `DAHWbajWAMg` | só para comparar; imagens planas |

No arquivo de edição, os textos estão em **Inter** e os rótulos em **Roboto Mono**, fontes
nativas do Canva e quase gêmeas da Geist. No vídeo final continua a Geist. Logos e textos
vazados são imagens: dá para mover, redimensionar, trocar ou apagar.

**Replicação:** `canva-baseline.json` guarda o estado inicial de cada elemento (texto, posição,
tamanho, cor). Quando as edições terminarem, o design é lido de novo, comparado com essa base
e cada mudança é aplicada em `brand-film.html`; depois o vídeo é renderizado de novo.

## Outros programas

- **Canva:** *Criar design → Importar arquivo →* `brand-film-cenas.pdf`. Cada página vira um design com textos e formas editáveis.
- **Illustrator / Affinity:** abra o PDF direto; o texto é texto de verdade.
- **Photoshop / Figma / celular:** use os PNGs. Pode editar por cima ou só rabiscar e anotar com setas.

A fonte é a **Geist** (gratuita no Google Fonts). Se o programa trocar por outra, tudo bem: no vídeo final eu uso a Geist.

## O que você pode mudar

- textos e números (troque pelos dados reais dos seus cases)
- cores, tamanhos e posições
- tirar, adicionar ou trocar elementos (pode colar fotos, prints e mockups)
- a ordem das cenas: renumere os arquivos

**Mantenha 1080×1920 e o número no começo do nome** (`07_…`) para eu saber qual cena é.
Tempo de cena, ritmo e música: me diga por escrito, por exemplo "cena 12 com 2 segundos".

## Como devolver

Mande aqui no chat só as cenas que mudaram (PNG, JPG ou as páginas do PDF),
com qualquer observação. Eu aplico na animação, renderizo e devolvo o vídeo.
