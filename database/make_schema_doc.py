"""Generate database/SCHEMA.md from the live battery_db.

Run from the project root:  python database/make_schema_doc.py
Everything about tables, columns, keys and constraints is read from PostgreSQL itself,
so it always matches the real database. The design notes at the end are written by hand.
"""
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402

TABLES_SQL = """
SELECT c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r'
ORDER BY c.relname
"""

COLUMNS_SQL = """
SELECT c.relname, a.attname, format_type(a.atttypid, a.atttypmod) AS col_type,
       NOT a.attnotnull AS nullable, pg_get_expr(d.adbin, d.adrelid) AS col_default,
       a.attidentity
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
WHERE n.nspname = 'public' AND c.relkind = 'r' AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY c.relname, a.attnum
"""

CONSTRAINTS_SQL = """
SELECT conrelid::regclass::text AS tbl, contype, conname, pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY 1, 2, 3
"""

FK_EDGES_SQL = """
SELECT confrelid::regclass::text AS parent, conrelid::regclass::text AS child,
       (SELECT string_agg(a.attname, ', ' ORDER BY a.attnum) FROM pg_attribute a
         WHERE a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)) AS cols
FROM pg_constraint c
WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace
ORDER BY 1, 2
"""

VIEWS_SQL = "SELECT viewname FROM pg_views WHERE schemaname = 'public' ORDER BY 1"

TRIGGERS_SQL = """
SELECT DISTINCT event_object_table, trigger_name
FROM information_schema.triggers WHERE trigger_schema = 'public' ORDER BY 1, 2
"""

INDEXES_SQL = """
SELECT tablename, indexname, indexdef FROM pg_indexes
WHERE schemaname = 'public'
  AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = indexname
                  AND connamespace = 'public'::regnamespace)
ORDER BY 1, 2
"""

KIND = {"p": "Primary key", "u": "Unique", "f": "Foreign key", "c": "Check"}


def cell(value):
    return str(value).replace("|", "\\|") if value is not None else "-"


def main():
    with SessionLocal() as db:
        tables = [r[0] for r in db.execute(text(TABLES_SQL))]
        columns = db.execute(text(COLUMNS_SQL)).all()
        constraints = db.execute(text(CONSTRAINTS_SQL)).all()
        edges = db.execute(text(FK_EDGES_SQL)).all()
        views = [r[0] for r in db.execute(text(VIEWS_SQL))]
        triggers = db.execute(text(TRIGGERS_SQL)).all()
        indexes = db.execute(text(INDEXES_SQL)).all()

    cols_by_table = defaultdict(list)
    for rel, name, col_type, nullable, default, identity in columns:
        extra = "generated identity" if identity in ("a", "d") else default
        cols_by_table[rel].append((name, col_type, "yes" if nullable else "no", extra))

    cons_by_table = defaultdict(list)
    for tbl, kind, name, definition in constraints:
        cons_by_table[tbl].append((kind, name, definition))

    sql_files = sorted(p.name for p in HERE.glob("*.sql"))

    out = []
    out.append("# Database schema (PostgreSQL, database `battery_db`)")
    out.append("")
    out.append("Generated from the live database by `python database/make_schema_doc.py`.")
    out.append(f"{len(tables)} tables, {len(views)} views, {len(triggers)} trigger(s).")
    out.append("All sample rows in the database are synthetic and marked SAMPLE or SYNTHETIC.")
    out.append("")
    out.append("## Relationships")
    out.append("")
    out.append("Each line is one foreign key (parent on the left, child on the right). The diagram")
    out.append("is drawn by GitHub when you open this file in the repository.")
    out.append("")
    out.append("```mermaid")
    out.append("erDiagram")
    for parent, child, cols in edges:
        out.append(f'    {parent} ||--o{{ {child} : "{cols}"')
    out.append("```")
    out.append("")
    out.append("## Tables")
    out.append("")
    for t in tables:
        out.append(f"### {t}")
        out.append("")
        out.append("| Column | Type | Null | Default |")
        out.append("|---|---|---|---|")
        for name, col_type, nullable, extra in cols_by_table[t]:
            out.append(f"| `{name}` | {cell(col_type)} | {nullable} | {cell(extra)} |")
        out.append("")
        for kind in ("p", "u", "f", "c"):
            items = [d for k, _, d in cons_by_table[t] if k == kind]
            if items:
                out.append(f"{KIND[kind]}:")
                for d in items:
                    out.append(f"- `{d}`")
                out.append("")
    if views:
        out.append("## Views")
        out.append("")
        for v in views:
            out.append(f"- `{v}`")
        out.append("")
    if triggers:
        out.append("## Triggers")
        out.append("")
        for table, name in triggers:
            out.append(f"- `{name}` on `{table}`")
        out.append("")
    if indexes:
        out.append("## Extra indexes (besides keys)")
        out.append("")
        for table, name, definition in indexes:
            out.append(f"- `{name}` on `{table}`: `{definition}`")
        out.append("")
    out.append("## SQL files, in the order they are run")
    out.append("")
    for f in sql_files:
        out.append(f"1. `database/{f}`")
    out.append("")
    out.append(NOTES)

    (HERE / "SCHEMA.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote database/SCHEMA.md: {len(tables)} tables, {len(views)} views, "
          f"{len(triggers)} trigger(s), {len(indexes)} extra indexes, {len(sql_files)} SQL files")


NOTES = """## Design notes (written by hand)

- **Lookup tables**: `manufacturer`, `chemistry`, `data_source` and `alert_priority` hold each
  name or allowed value once; other tables point to them with a foreign key instead of
  repeating the text.
- **Weak entities**: `temperature_reading`, `coolant_flow` and `electrical_reading` have no
  id of their own. A reading is identified by its sensor and its time (composite primary key
  `sensor_id` + `recorded_at`).
- **One to one**: `digital_twin.battery_id` is UNIQUE, so a battery has at most one twin.
- **Many to many**: `model_training` links `ai_model` and `training_dataset`.
- **Derived values are not stored**: state of health is `capacity_ah / nominal_capacity_ah`,
  calculated when it is asked for, so it can never disagree with the stored capacity.
- **Prediction chain**: `ai_model` -> `prediction_result` (raw model label) -> `risk_assessment`
  (final level after the safety rule) -> `alert` and `recommendation`. `feedback` points to a
  `prediction_result`; `model_performance` points to an `ai_model`.
- **Rules live in the database**: allowed values and ranges are CHECK constraints, and a
  trigger creates an alert when a risk assessment is HIGH or CRITICAL, so the rules hold
  no matter which program writes the data.
- **Deleting**: almost every foreign key is NO ACTION, so a row that is still referenced cannot
  be deleted (the API answers 409). Only `feedback` and `model_performance` are removed
  automatically with their parent.
- **Normalization reasoning** (explain this in the viva, and check it against your own notes):
  no repeating groups or multi-valued columns (1NF); tables with a single-column key cannot have
  partial dependencies, and in the reading tables the value columns depend on the whole
  (sensor, time) key (2NF); descriptive data lives in the lookup tables instead of being copied
  into rows, so non-key columns do not depend on other non-key columns (3NF).
"""

main()
