#!/usr/bin/env python3
"""
Create a minimal SQLite test database that mirrors the current_collection schema.

Populates all four tables (bib, item, hold, bib_record_item_record_link) with
enough realistic sample data that every canned query in metadata.yml returns rows.

Usage:
    uv run python scripts/create-test-db.py [output_path]

    output_path defaults to test.db in the project root.
"""

import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "test.db"


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bib (
            bib_record_id       INTEGER PRIMARY KEY,
            bib_record_num      TEXT,
            control_numbers     TEXT,
            isbn                TEXT,
            best_author         TEXT,
            best_title          TEXT,
            publisher           TEXT,
            publish_year        INTEGER,
            bib_level_callnumber TEXT,
            indexed_subjects    TEXT
        );

        CREATE TABLE IF NOT EXISTS item (
            item_record_id      INTEGER PRIMARY KEY,
            item_record_num     TEXT,
            bib_record_id       INTEGER REFERENCES bib(bib_record_id),
            bib_record_num      TEXT,
            creation_date       TEXT,
            record_last_updated TEXT,
            barcode             TEXT,
            location_code       TEXT,
            checkout_date       TEXT,
            due_date            TEXT,
            patron_branch_code  TEXT,
            last_checkout_date  TEXT,
            last_checkin_date   TEXT,
            checkout_total      INTEGER,
            renewal_total       INTEGER,
            isbn                TEXT,
            item_format         TEXT,
            item_status_code    TEXT,
            price               REAL,
            item_callnumber     TEXT
        );

        CREATE TABLE IF NOT EXISTS hold (
            bib_record_id   INTEGER REFERENCES bib(bib_record_id),
            bib_record_num  TEXT,
            holds           TEXT
        );

        CREATE TABLE IF NOT EXISTS bib_record_item_record_link (
            bib_record_id   INTEGER REFERENCES bib(bib_record_id),
            item_record_id  INTEGER REFERENCES item(item_record_id)
        );
    """)


def populate(conn: sqlite3.Connection) -> None:
    today = date.today()
    recent = (today - timedelta(days=10)).isoformat()
    old = (today - timedelta(days=400)).isoformat()

    bibs = [
        # (bib_record_id, bib_record_num, control_numbers, isbn,
        #  best_author, best_title, publisher, publish_year,
        #  bib_level_callnumber, indexed_subjects)
        (1001, "b10010001", "ocn000559474", "9780525559474",
         "Greer, Germaine", "The Female Eunuch",
         "McGraw-Hill", 1970, "HQ1121 .G68", "Feminism; Women -- Social conditions"),
        (1002, "b10020002", "ocn000528379", "9780374528379",
         "Fitzgerald, F. Scott", "The Great Gatsby",
         "Scribner", 1925, "PS3511.I9 G7", "Fiction; Satire"),
        (1003, "b10030003", "ocn000316097", "9780062316097",
         "Lee, Harper", "To Kill a Mockingbird",
         "HarperCollins", 1960, "PS3562.E353 T6", "Fiction; Race relations"),
        (1004, "b10040004", "ocn000490818", "9780385490818",
         "Morrison, Toni", "Beloved",
         "Knopf", 1987, "PS3563.O8749 B45", "Fiction; Slavery"),
        (1005, "b10050005", "ocn001148843", "9781982148843",
         "Kendi, Ibram X.", "How to Be an Antiracist",
         "One World", 2019, "E185.615 .K46", "Racism; Antiracism"),
    ]

    conn.executemany("INSERT INTO bib VALUES (?,?,?,?,?,?,?,?,?,?)", bibs)

    # Two items per bib; mix of branches, formats, statuses
    # CHPL branch codes: mapl=Main, green=Green Township, norw=Norwood,
    #                    hyde=Hyde Park, west=Westwood
    items = [
        # item_record_id, item_record_num, bib_record_id, bib_record_num,
        # creation_date, record_last_updated, barcode, location_code,
        # checkout_date, due_date, patron_branch_code,
        # last_checkout_date, last_checkin_date,
        # checkout_total, renewal_total, isbn, item_format,
        # item_status_code, price, item_callnumber

        # bib 1001 — checked out + available
        (2001, "i20010001", 1001, "b10010001", old, old,
         "31819000000001", "mapl ", None, None, None,
         old, old, 42, 5, "9780525559474", "Book", "-", 18.99, "HQ1121 .G68"),
        (2002, "i20020002", 1001, "b10010001", old, old,
         "31819000000002", "green", today.isoformat(), (today + timedelta(days=21)).isoformat(), "mapl ",
         old, old, 31, 3, "9780525559474", "Book", "o", 18.99, "HQ1121 .G68"),

        # bib 1002 — both available
        (2003, "i20030003", 1002, "b10020002", old, old,
         "31819000000003", "norw ", None, None, None,
         old, old, 88, 12, "9780374528379", "Book", "-", 14.95, "PS3511.I9 G7"),
        (2004, "i20040004", 1002, "b10020002", old, old,
         "31819000000004", "hyde ", None, None, None,
         old, old, 67, 8, "9780374528379", "Book", "-", 14.95, "PS3511.I9 G7"),

        # bib 1003 — DVD + Book
        (2005, "i20050005", 1003, "b10030003", old, old,
         "31819000000005", "mapl ", None, None, None,
         old, old, 120, 15, "9780062316097", "DVD", "-", 24.99, "PS3562.E353 T6"),
        (2006, "i20060006", 1003, "b10030003", old, old,
         "31819000000006", "west ", None, None, None,
         old, old, 95, 10, "9780062316097", "Book", "-", 14.00, "PS3562.E353 T6"),

        # bib 1004 — Audiobook + Book, recently added
        (2007, "i20070007", 1004, "b10040004", recent, recent,
         "31819000000007", "mapl ", None, None, None,
         recent, recent, 3, 0, "9780385490818", "Audiobook", "-", 34.99, "PS3563.O8749 B45"),
        (2008, "i20080008", 1004, "b10040004", recent, recent,
         "31819000000008", "norw ", None, None, None,
         None, None, 0, 0, "9780385490818", "Book", "-", 17.00, "PS3563.O8749 B45"),

        # bib 1005 — eBook + Book, recently added, high holds
        (2009, "i20090009", 1005, "b10050005", recent, recent,
         "31819000000009", "mapl ", None, None, None,
         recent, None, 5, 1, "9781982148843", "eBook", "-", 0.00, "E185.615 .K46"),
        (2010, "i20100010", 1005, "b10050005", recent, recent,
         "31819000000010", "green", today.isoformat(), (today + timedelta(days=14)).isoformat(), "green",
         recent, recent, 22, 2, "9781982148843", "Book", "o", 28.00, "E185.615 .K46"),
    ]

    conn.executemany("""
        INSERT INTO item VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    """, items)

    # Holds — semicolon-delimited hold detail strings (Sierra format)
    # hold_count = len(holds.split(';'))
    holds = [
        (1005, "b10050005",
         "p12345;p12346;p12347;p12348;p12349;p12350;p12351;p12352"),   # 8 holds
        (1003, "b10030003",
         "p22345;p22346;p22347;p22348;p22349"),                         # 5 holds
        (1004, "b10040004",
         "p32345;p32346;p32347"),                                        # 3 holds
        (1001, "b10010001",
         "p42345;p42346"),                                               # 2 holds
    ]

    conn.executemany("""
        INSERT INTO hold VALUES (?, ?, ?)
    """, holds)

    # Link table
    links = [(b, i) for i, b in [(2001, 1001), (2002, 1001),
                                   (2003, 1002), (2004, 1002),
                                   (2005, 1003), (2006, 1003),
                                   (2007, 1004), (2008, 1004),
                                   (2009, 1005), (2010, 1005)]]
    conn.executemany("""
        INSERT INTO bib_record_item_record_link VALUES (?, ?)
    """, links)


def verify_canned_queries(conn: sqlite3.Connection) -> None:
    """Run all canned queries from metadata.yml and assert they return rows."""
    queries = {
        "items_by_branch": """
            SELECT location_code, COUNT(*) AS item_count
            FROM item GROUP BY location_code ORDER BY item_count DESC
        """,
        "top_holds": """
            SELECT b.best_title, b.best_author, b.publish_year,
                   length(h.holds) - length(replace(h.holds, ';', '')) + 1 AS hold_count
            FROM hold AS h
            JOIN bib AS b ON b.bib_record_id = h.bib_record_id
            ORDER BY hold_count DESC LIMIT 50
        """,
        "most_checked_out": """
            SELECT b.best_title, b.best_author, i.location_code,
                   i.item_format, i.checkout_total
            FROM item AS i
            JOIN bib AS b ON b.bib_record_id = i.bib_record_id
            ORDER BY i.checkout_total DESC LIMIT 100
        """,
        "available_items_by_format": """
            SELECT item_format, COUNT(*) AS available_count
            FROM item WHERE item_status_code = '-'
            GROUP BY item_format ORDER BY available_count DESC
        """,
        "recently_added": """
            SELECT b.best_title, b.best_author, i.item_format,
                   i.location_code, i.creation_date
            FROM item AS i
            JOIN bib AS b ON b.bib_record_id = i.bib_record_id
            WHERE i.creation_date >= date('now', '-30 days')
            ORDER BY i.creation_date DESC LIMIT 200
        """,
    }

    all_ok = True
    for name, sql in queries.items():
        rows = conn.execute(sql).fetchall()
        status = "OK" if rows else "EMPTY — no rows returned!"
        print(f"  {name}: {len(rows)} row(s) — {status}")
        if not rows:
            all_ok = False

    if not all_ok:
        print("\nERROR: one or more canned queries returned no rows.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_PATH
    output.unlink(missing_ok=True)

    print(f"Creating test database: {output}")
    conn = sqlite3.connect(output)
    try:
        create_schema(conn)
        populate(conn)
        conn.commit()
        print("Verifying canned queries:")
        verify_canned_queries(conn)
    finally:
        conn.close()

    print(f"\nDone: {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
