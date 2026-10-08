import datetime as dt
import sqlite3

from .config import DATA_DIR
from .models import Oferta
from .utils import chave_similar

_DB = DATA_DIR / "ofertas.db"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB)
    c.execute(
        "CREATE TABLE IF NOT EXISTS postadas ("
        " uid TEXT PRIMARY KEY,"
        " plataforma TEXT,"
        " titulo TEXT,"
        " preco REAL,"
        " postada_em TEXT,"
        " chave TEXT)"
    )
    colunas = {linha[1] for linha in c.execute("PRAGMA table_info(postadas)")}
    if "chave" not in colunas:  # banco criado antes do dedupe de títulos
        c.execute("ALTER TABLE postadas ADD COLUMN chave TEXT")
    c.execute("CREATE INDEX IF NOT EXISTS idx_postadas_chave ON postadas (chave, postada_em)")
    return c


def ja_postada(uid: str, dentro_de_dias: int) -> bool:
    with _conn() as c:
        row = c.execute("SELECT postada_em FROM postadas WHERE uid = ?", (uid,)).fetchone()
    if not row:
        return False
    postada = dt.datetime.fromisoformat(row[0])
    return (dt.datetime.now() - postada) < dt.timedelta(days=dentro_de_dias)


def chave_recente(chave: str, dentro_de_dias: int) -> bool:
    """True se já foi postado algo com essa chave de título recentemente (qualquer plataforma)."""
    if not chave:
        return False
    limite = (dt.datetime.now() - dt.timedelta(days=dentro_de_dias)).isoformat(timespec="seconds")
    with _conn() as c:
        row = c.execute(
            "SELECT 1 FROM postadas WHERE chave = ? AND postada_em >= ? LIMIT 1",
            (chave, limite),
        ).fetchone()
    return row is not None


def registrar(oferta: Oferta) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO postadas (uid, plataforma, titulo, preco, postada_em, chave)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (oferta.uid, oferta.plataforma, oferta.titulo, oferta.preco,
             dt.datetime.now().isoformat(timespec="seconds"), chave_similar(oferta.titulo)),
        )


def postadas_hoje() -> int:
    with _conn() as c:
        return c.execute(
            "SELECT COUNT(*) FROM postadas WHERE date(postada_em) = date('now', 'localtime')"
        ).fetchone()[0]


def total_postadas() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM postadas").fetchone()[0]
