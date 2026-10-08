# Análise: bot-ofertas-telegram

**Data:** 08/10/2026  
**Projeto:** `C:\Meus Projetos\bot-ofertas-telegram`  
**Linguagem:** Python 3.12+ (gerenciado com `uv`)

---

## Visão geral do projeto

Bot que roda localmente no Windows, garimpa promoções em **Mercado Livre, Shopee e Amazon** e posta no canal do Telegram com links de afiliado do próprio usuário. Dois modos:

1. **Automático** — ciclos periódicos buscam ofertas, filtram por desconto mínimo, evitam repetição e postam as melhores com link de afiliado.
2. **Conversor** — o dono cola link de produto no privado; o bot monta prévia com link de afiliado e o dono decide ✅ Postar ou 🗑 Descartar.

Arquitetura modular em `ofertas/`:

```
ofertas/
├── main.py            # CLI (check, run, converter, postar, ml-login, testar, painel)
├── bot_interativo.py  # Bot Telegram (conversor + agendador de ciclos)
├── pipeline.py        # Coleta → filtros → links → postagem
├── formatter.py       # Visual do post (caption HTML)
├── db.py              # SQLite anti-repetição
├── config.py          # Lê .env + config.yaml
├── models.py          # Dataclass Oferta
├── utils.py           # Helpers (parse preço, sessão HTTP, URLs)
├── nichos.py          # Catálogo de nichos para painel
├── painel.py          # Painel web local (127.0.0.1:8481)
├── painel_html.py     # HTML do painel
├── telegram_poster.py # send_photo / send_message
└── sources/           # Fontes: mercadolivre.py, shopee.py, amazon.py
```

Cada fonte em `sources/` expõe o mesmo contrato (`e_link`, `buscar_ofertas`, `converter`), facilitando adicionar novas plataformas.

---

## Pontos fortes 👏

| Área | O que funciona bem |
|------|-------------------|
| **Arquitetura** | Fontes plugáveis, configuração separada de segredos (`.env`) e ajustes (`config.yaml`), painel web que esconde terminal do usuário leigo. |
| **Estratégias por plataforma** | Shopee: Open API oficial. Amazon: Creators API + fallback para scraping. Mercado Livre: Linkbuilder via sessão logada persistente (Playwright). |
| **Educação com os sites** | `time.sleep` entre páginas, rodízio de tarefas na Amazon, detecção de captcha/bloqueio com abort de ciclo. |
| **Dedupe** | `uid` único por plataforma + ID, `_chave_similar` (5 primeiras palavras) dentro do ciclo, alternância de plataformas no `escolher()`. |
| **Segurança** | `.gitignore` cobre `.env` e `data/` (cookies do ML ficam fora do git). |

---

## Ideias de melhoria (9 frentes)

### 1. Curadoria — postar coisa melhor (alto impacto no canal)
- **Desconto mínimo em R$** — Hoje só `%` (`desconto_minimo: 25`), prioriza barbadinhas de R$ 8 com 90% off. Um `desconto_minimo_reais: 30` filtraria por economia absoluta.
- **Score em vez de % puro** — `escolher()` ordena só por desconto %. Um score `(desconto% × poupança em R$) + bônus por avaliação` escolheria ofertas mais atraentes.
- **Dedupe "similar" entre ciclos** — `_chave_similar` só vale dentro de um ciclo; variações (cor/tamanho) podem ser repostadas dias depois. Salvar a chave no SQLite resolve.
- **Dedupe entre plataformas** — Mesmo produto na ML e na Shopee vira 2 posts. Comparar título/chave entre fontes no `escolher()`.
- **Limite diário** — Existe `max_posts_por_ciclo`, mas não `max_posts_por_dia` — PC ligado + ciclos de 45 min pode inundar o canal.
- **Re-checar preço antes de postar** — No modo conversor, preço pode estar defasado. Validação leve antes do post evita preço errado no canal.

### 2. Monitor de preço (recurso diferencial) 📉
Guardar `message_id` no SQLite abre portas:
- Preço **caiu**? Edita caption ou posta "🔴 AINDA MAIS BARATO".
- **Subiu / acabou estoque**? Deleta o post automaticamente (canal honesto).
- Bônus: apagar posts antigos (canal sempre fresco).

### 3. Bot no Telegram — comandos e UX 🤖
- `/pausar` e `/retomar` os ciclos (hoje só desligando processo).
- `/status` mais rico: último post, próximo ciclo (job_queue expõe `next run time`), ofertas coletadas vs. postadas.
- **Fila de aprovação**: melhores ofertas do ciclo vão ao privado do dono com ✅/🗑 (reaproveitando `_pendentes`).
- Botões customizados no post ("🛒 Pegar oferta" já existe).

### 4. Compliance ⚖️
Amazon exige divulgação **por link/post**, não só na bio. Uma linha no `formatter.py` (configurável): *"📌 Link de afiliado — podemos receber comissão, sem custo extra pra você."* Barato e evita ban da conta.

### 5. Painel 🖥️
- **Editar `config.yaml` pelo painel**: hoje só `.env` + nichos; `intervalo`, `desconto_minimo`, `palavras_bloqueadas`, `horário` exigem bloco de notas + reinício.
- Botão **"Rodar ciclo agora"** e **prévia de post** (montar caption no navegador antes de postar).
- **Página de estatísticas**: posts por dia/plataforma, últimos 20 posts do SQLite, repostar/excluir.
- Hoje painel não tem ação `ciclo` no mapa `/api/acao` — adição trivial.

### 6. Robustez e manutenção 🛡️
- **Zero testes**. Parseadores (`parse_preco_br`, `_parse_card`, `_chave_similar`, `escolher`, `formatter`) são puramente lógicos e quebram quando sites mudam layout — testes com HTML fixtures dariam rede de segurança barata.
- **Log em arquivo** (`data/logs/` com `RotatingFileHandler`) — hoje só stdout; rodando via `run.bat` não fica histórico.
- **Tratar `RetryAfter`** (flood do Telegram) em `postar_oferta` com retry em vez de perder o post.
- **Hot-reload da config**: `config = Config()` roda no import; reler a cada ciclo tornaria "editar e aplicar" instantâneo.
- Ruff + mypy + GitHub Actions — o repo já é git.

### 7. Performance ⚡
- **Coletar as 3 fontes em paralelo** (`ThreadPoolExecutor`): ciclo mais rápido, preços menos defasados.
- **Reusar contexto Playwright** entre conversões ML (hoje cada link abre Chrome headless novo).
- Persistir `_rodizio` da Amazon (reset ao reiniciar volta sempre à página 1).

### 8. Ideias maiores 🚀
- **Novas fontes**: AliExpress (tem API oficial de afiliado!), Kabum, Magalu — arquitetura já comporta.
- **Multi-canal**: postar nichos diferentes em canais diferentes (ex.: canal tech + canal casa).
- **Legendas com IA**: projeto irmão `ofertas-ia-mvp` (n8n) — uma linha chamativa gerada por LLM por post, com fallback ao formato atual.
- **Banner de preço na imagem** (Pillow): baixar foto e carimbar "De R$ X — Por R$ Y" antes do `send_photo` (também evita falhas do Telegram ao buscar URL da imagem).
- **Instalar como tarefa do Windows** (`schtasks`) em vez do loop do `run.bat` — sobrevive a logout.

### 9. Observações/bugs pontuais 🔍
- `painel.detectar_ids()` usa `getUpdates` — se o bot estiver rodando ao mesmo tempo, os dois disputam updates (pode dar 409/vazio). Vale avisar na UI ou parar o bot antes.
- No callback `_callback`, se `TELEGRAM_CHAT_ID` estiver vazio, `postar_oferta` explode sem tratamento.
- `_pendentes` nunca expira tokens (vazamento trivial de memória, inofensivo na prática).

---

## Plano aprovado: Curadoria + Compliance

**Objetivo:** melhorar qualidade do canal com mudanças pequenas, localizadas, zero breaking changes (defaults preservam comportamento atual).

**6 mudanças · 4 arquivos editados + testes · ~60 linhas novas**

### 1. Filtro de economia mínima em R$ (`filtros.desconto_minimo_reais`)
- `config.yaml`: `desconto_minimo_reais: 0` (0 = desligado)
- `config.py`: `self.desconto_minimo_reais: float`
- `pipeline.filtrar()`: descarta se `preco` e `preco_original` existem e `(preco_original - preco) < desconto_minimo_reais`
- **Leniente**: oferta sem `preco_original` passa pelo filtro (o % continua sendo o filtro dela).

### 2. Critério de ordenação configurável (`filtros.ordenar_por`)
- `config.yaml`: `ordenar_por: desconto` — valores: `desconto` (%) ou `poupanca` (R$ de economia, desconto como desempate)
- `config.py`: `self.ordenar_por: str`
- `models.py`: nova property `@property def poupanca(self) -> float` (`preco_original - preco` ou 0)
- `pipeline.escolher()`: usa `_chave_ordem` baseada em `config.ordenar_por`

### 3. Dedupe de títulos parecidos entre ciclos
- Move `_chave_similar` → `utils.chave_similar` (evita import circular)
- `db.py`: coluna `chave` em `postadas` + migração automática (`ALTER TABLE` se não existe) + índice `(chave, postada_em)` + `registrar()` grava a chave + `chave_recente(chave, dias)`
- `pipeline.filtrar()`: depois de `ja_postada`, checa `db.chave_recente(chave_similar(titulo), config.dedupe_titulos_dias)`
- `config.yaml` + `config.py`: `dedupe_titulos: true`, `dedupe_titulos_dias: 3` (mais curto que `nao_repetir_dias: 7`)
- **Migração**: linhas antigas ficam com `chave = NULL` e nunca bloqueiam (`WHERE chave = ?` ignora NULL) — sem backfill necessário.

### 4. Limite diário de posts (`geral.max_posts_por_dia`)
- `config.yaml`: `max_posts_por_dia: 30` (0 = sem limite)
- `config.py`: `self.max_posts_por_dia: int`
- `db.py`: `postadas_hoje() -> int` — `COUNT(*) WHERE date(postada_em) = date('now','localtime')`
- `pipeline.executar_ciclo()`: calcula `vagas = max_posts_por_ciclo`; se `max_posts_por_dia > 0`, `vagas = min(vagas, max_posts_por_dia - postadas_hoje())`; se `vagas <= 0`, loga e retorna 0
- `bot_interativo._cmd_status`: mostra "🗓 Hoje: X/Y posts"

### 5. Divulgação de afiliado por post (compliance Amazon) ⚖️
- `config.yaml`: `divulgar_afiliado: true`
- `config.py`: flag booleana
- `formatter.montar_caption()`: última linha `📌 <i>Link de afiliado — pode gerar comissão pela indicação, sem custo extra pra você.</i>`
- Caption de foto tem limite 1024 chars; atuais ficam em ~250, sobra folga.

### 6. Testes (rede de segurança para 1–5)
- Novo `tests/` com `pytest`
- `pyproject.toml`: `[dependency-groups] dev = ["pytest>=8.0"]` + `[tool.pytest.ini_options] pythonpath = ["."] testpaths = ["tests"]`
- `tests/conftest.py`: fixtures `nova_oferta`, `cfg` (config determinística), `banco` (SQLite temporário via `tmp_path`)
- `tests/test_filtrar.py`: desconto %, economia R$, dedupe por uid e por chave, palavras bloqueadas, sem título, preço min/max
- `tests/test_escolher.py`: ordena por desconto (padrão), por poupança, alterna plataformas, pula variações
- `tests/test_formatter.py`: caption com de/por, divulgação on/off, escape HTML, formato BR
- `tests/test_db.py`: registrar/ja_postada, expiração, chave_recente, postadas_hoje, migração banco antigo sem coluna `chave`

---

## `config.yaml` final (trecho novo)

```yaml
geral:
  max_posts_por_dia: 30         # teto de posts por dia, somando todos os ciclos (0 = sem limite)
  divulgar_afiliado: true       # aviso de afiliado no fim de cada post

filtros:
  desconto_minimo_reais: 0      # ex: 30 = exija no mínimo R$30 de economia
  ordenar_por: desconto         # "desconto" (%) ou "poupanca" (R$ economizados)
  dedupe_titulos: true          # pular ofertas com título muito parecido com post recente
  dedupe_titulos_dias: 3        # janela do dedupe de títulos, em dias
```

---

## Decisões confirmadas (defaults)

| Decisão | Escolha |
|---------|---------|
| `ordenar_por` default | `desconto` (comportamento atual preservado; usuário muda no yaml se quiser) |
| Texto da divulgação | `"Link de afiliado — pode gerar comissão pela indicação, sem custo extra pra você."` |
| `max_posts_por_dia` default | `30` (razoável para canais ativos) |

---

## Próximos passos (fora deste pacote)

1. **Monitor de preço** (precisa `message_id` no DB + job de verificação)
2. **Painel completo** (editar config.yaml, botão ciclo, prévia, estatísticas)
3. **Comandos no Telegram** (`/pausar`, `/retomar`, fila de aprovação)
4. **Robustez/testes adicionais** (log em arquivo, RetryAfter, hot-reload, CI)
5. **Novas fontes / IA** (AliExpress, legendas LLM, banner na imagem)