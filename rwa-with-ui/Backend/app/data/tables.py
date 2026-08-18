"""Loads the mock source tables.

Everything the agents query comes from a single Excel workbook
(data/Main Data.xlsx), one sheet per table. There is no database connection
anywhere in this application.

The workbook is read once and cached; the previous implementation re-read it on
every request.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.settings import SOURCE_TABLES_FILE

# Sheet names in the workbook, in workbook order. This is the authoritative
# list of table names the agents may reference.
TABLE_NAMES: tuple[str, ...] = (
    "om_cdm_rwa_mtrc",
    "om_cdm_rwa_mtrc_extn",
    "dsft_conc_txn_result",
    "dsft_conc_result_txn_map",
    "dsft_conc_result",
    "dsft_fi_base_subassetclass",
)

# Table used when a check step does not name one explicitly.
DEFAULT_TABLE_NAME = "om_cdm_rwa_mtrc"


class SourceDataError(RuntimeError):
    """Raised when the source workbook is missing or a sheet cannot be read."""


@lru_cache(maxsize=1)
def load_tables() -> dict[str, pd.DataFrame]:
    """Return every source table as a DataFrame, keyed by table name."""
    if not SOURCE_TABLES_FILE.exists():
        raise SourceDataError(
            f"Source tables workbook not found at {SOURCE_TABLES_FILE}. "
            f"Set RWA_SOURCE_TABLES_FILE to override the location."
        )
    try:
        frames = pd.read_excel(SOURCE_TABLES_FILE, sheet_name=list(TABLE_NAMES))
    except ValueError as exc:
        raise SourceDataError(
            f"Could not read the expected sheets from {SOURCE_TABLES_FILE}: {exc}"
        ) from exc
    return frames


def get_table(table_name: str) -> pd.DataFrame:
    """Return one source table by name."""
    tables = load_tables()
    if table_name not in tables:
        raise SourceDataError(
            f"Unknown table {table_name!r}. Known tables: {', '.join(TABLE_NAMES)}"
        )
    return tables[table_name]


def reset_cache() -> None:
    """Force the workbook to be re-read on the next call."""
    load_tables.cache_clear()
