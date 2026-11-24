#!/usr/bin/env bash
# Instala a página EXP + Bipa em expdigital.io/bipa (site Next.js).
# Uso: curl -fsSL <url deste arquivo> | bash
# Opcional: SITE_DIR=/caminho/do/site para não procurar automaticamente.
set -euo pipefail

BASE="https://raw.githubusercontent.com/Expdigital-IO/EXP-SO/claude/project-thread-4p3r56/site/bipa"
say(){ printf '\n\033[1;38;5;202m▸ %s\033[0m\n' "$*"; }
die(){ printf '\n\033[1;31m✖ %s\033[0m\n' "$*" >&2; exit 1; }

# 1. Acha o projeto Next.js do site
if [ -z "${SITE_DIR:-}" ]; then
  say "Procurando o projeto Next.js do site..."
  mapfile -t CANDS < <(find /var/www /srv /opt /home /root -maxdepth 5 -name package.json \
      -not -path '*/node_modules/*' -not -path '*/.next/*' 2>/dev/null \
    | xargs -r grep -l '"next"' 2>/dev/null | xargs -r -n1 dirname | sort -u)
  # prefere o que menciona expdigital
  PREF=()
  for d in "${CANDS[@]:-}"; do [ -n "$d" ] && grep -rqsi --include='*.tsx' --include='*.ts' --include='*.js' --include='*.jsx' -m1 'expdigital' "$d/src" "$d/app" "$d/pages" "$d/components" 2>/dev/null && PREF+=("$d"); done
  [ ${#PREF[@]} -gt 0 ] && CANDS=("${PREF[@]}")
  if [ ${#CANDS[@]} -eq 0 ] || [ -z "${CANDS[0]:-}" ]; then die "Não achei o projeto. Rode de novo com SITE_DIR=/caminho/do/site"; fi
  if [ ${#CANDS[@]} -gt 1 ]; then printf '  %s\n' "${CANDS[@]}"; die "Achei mais de um projeto. Rode de novo com SITE_DIR=<um dos caminhos acima>"; fi
  SITE_DIR="${CANDS[0]}"
fi
cd "$SITE_DIR" || die "Pasta $SITE_DIR não existe"
say "Site: $SITE_DIR"

# 2. Baixa a página
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
curl -fsSL "$BASE/index.html" -o "$TMP" || die "Falha ao baixar a página"
grep -q 'business.bipa.app/signup?ref=EXPDIGITAL' "$TMP" || die "Arquivo baixado não parece a página da Bipa"

# 3. Cria a rota /bipa (App Router ou Pages Router), com o HTML embutido
EXT=js; [ -f tsconfig.json ] && EXT=ts
HTML_JSON="$(node -e 'process.stdout.write(JSON.stringify(require("fs").readFileSync(process.argv[1],"utf8")))' "$TMP")"
CREATED=""
if   [ -d src/app ]; then APPDIR=src/app
elif [ -d app ];     then APPDIR=app
else APPDIR=""; fi

if [ -n "$APPDIR" ]; then
  [ -e "$APPDIR/bipa" ] && die "Já existe $APPDIR/bipa. Remova ou renomeie antes de rodar."
  mkdir -p "$APPDIR/bipa"
  CREATED="$APPDIR/bipa/route.$EXT"
  cat > "$CREATED" <<EOF
// Página EXP + Bipa (gerada por install.sh). HTML completo servido como está.
export const dynamic = 'force-static';
const HTML = $HTML_JSON;
export function GET() {
  return new Response(HTML, { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' } });
}
EOF
  CLEAN="$APPDIR/bipa"
else
  PDIR=pages; [ -d src/pages ] && PDIR=src/pages
  [ -d "$PDIR" ] || die "Não achei app/ nem pages/ em $SITE_DIR"
  ls "$PDIR"/bipa.* "$PDIR"/bipa 2>/dev/null && die "Já existe uma página bipa em $PDIR."
  CREATED="$PDIR/bipa.js"
  cat > "$CREATED" <<EOF
// Página EXP + Bipa (gerada por install.sh). HTML completo servido como está.
const HTML = $HTML_JSON;
export async function getServerSideProps({ res }) {
  res.setHeader('content-type', 'text/html; charset=utf-8');
  res.setHeader('cache-control', 'public, max-age=300');
  res.end(HTML);
  return { props: {} };
}
export default function Bipa() { return null; }
EOF
  CLEAN="$CREATED"
fi
say "Rota criada: $CREATED"

# 4. Build + reinício
PM=npm; [ -f pnpm-lock.yaml ] && PM=pnpm; [ -f yarn.lock ] && PM=yarn
if [ -f docker-compose.yml ] || [ -f compose.yml ] || [ -f compose.yaml ] || [ -f docker-compose.yaml ]; then
  if [ ! -d node_modules ]; then
    say "Projeto roda em Docker: reconstruindo com docker compose..."
    docker compose up -d --build || { rm -rf "$CLEAN"; die "Build falhou. Rota removida, site intacto."; }
    say "Pronto! Abra https://expdigital.io/bipa"; exit 0
  fi
fi
say "Rodando build ($PM run build)..."
$PM run build || { rm -rf "$CLEAN"; die "Build falhou. Rota removida, nada mudou no site."; }

if command -v pm2 >/dev/null 2>&1; then
  ID="$(pm2 jlist 2>/dev/null | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const l=JSON.parse(s);const p=l.find(x=>x.pm2_env&&x.pm2_env.pm_cwd&&require("path").resolve(x.pm2_env.pm_cwd)===require("path").resolve(process.argv[1]));if(p)process.stdout.write(String(p.pm_id))}catch(e){}})' "$SITE_DIR")"
  if [ -n "$ID" ]; then say "Reiniciando pm2 (id $ID)..."; pm2 restart "$ID" --update-env; say "Pronto! Abra https://expdigital.io/bipa"; exit 0; fi
fi
say "Build ok. Reinicie o serviço do site do jeito que você costuma (pm2/systemd) e abra https://expdigital.io/bipa"
