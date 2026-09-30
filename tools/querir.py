"""Interroge l'index de consultation (voir index_corpus.py).

Usage :
  python tools/querir.py "rupture de bloc"           # recherche
  python tools/querir.py "kser" --kind pdf_page      # filtrer par type
  python tools/querir.py "nurbs" --n 10              # plus de résultats
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import sqlite3

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "corpus-index.db"


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--kind", default=None,
                    help="pdf_page / fiche / idee / casquette / projet")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--full", action="store_true", help="texte complet des blocs")
    args = ap.parse_args()

    if not DB.exists():
        print("index absent — lance tools/index_corpus.py")
        return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    safe = re.sub(r"[^\wà-ÿÀ-Ÿ\s]", " ", args.query).strip()
    sql = ("SELECT d.kind, d.ref, d.title, bm25(docs_fts) rank, "
           "snippet(docs_fts, 1, '▶', '◀', ' … ', 48) snip, "
           "LENGTH(d.text) len FROM docs_fts f JOIN docs d ON d.id = f.rowid "
           "WHERE docs_fts MATCH ?")
    params = [safe]
    if args.kind:
        sql += " AND d.kind = ?"
        params.append(args.kind)
    sql += " ORDER BY rank LIMIT ?"
    params.append(args.n)
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print(f"auncun résultat pour « {args.query} »")
        return
    for r in rows:
        print(f"[{r['kind']:9}] {r['title'][:60]}  (bm25 {r['rank']:.2f}, {r['len']} car)")
        print(f"           {r['ref']}")
        print(f"           {r['snip']}")
        if args.full:
            full = conn.execute("SELECT text FROM docs WHERE ref=? AND kind=?",
                                (r["ref"], r["kind"])).fetchone()
            if full:
                print("           ───── texte ─────")
                for line in full["text"].splitlines()[:40]:
                    print("           " + line)
        print()
    conn.close()


import re  # noqa: E402

if __name__ == "__main__":
    main()
