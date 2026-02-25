"""Unit tests for collection_analysis.extract — uses mock PostgreSQL connections."""

from unittest.mock import MagicMock

import pytest

from collection_analysis import extract
from collection_analysis.extract import _load_sql

_ALL_QUERY_NAMES = [
    "record_metadata",
    "bib",
    "item",
    "bib_record",
    "volume_record",
    "item_message",
    "language_property",
    "bib_record_item_record_link",
    "volume_record_item_record_link",
    "location",
    "location_name",
    "branch_name",
    "branch",
    "country_property_myuser",
    "item_status_property",
    "itype_property",
    "bib_level_property",
    "material_property",
    "hold",
    "circ_agg",
    "circ_leased_items",
]


class TestLoadSql:
    def test_returns_nonempty_string(self):
        assert len(_load_sql("record_metadata")) > 0

    def test_all_sql_files_loadable(self):
        for name in _ALL_QUERY_NAMES:
            sql = _load_sql(name)
            assert len(sql) > 0, f"Empty SQL file: {name}.sql"

    def test_item_message_regex_fix(self):
        sql = _load_sql("item_message")
        assert "(?:AM|PM)" not in sql, "Old SQLAlchemy-breaking pattern still present"
        assert "[AP]M" in sql, "Fixed character-class pattern missing"

    def test_missing_file_raises_file_not_found_error(self):
        with pytest.raises(FileNotFoundError):
            _load_sql("nonexistent_query_xyz")


def _make_mock_conn(rows_per_call):
    """
    Build a mock SQLAlchemy connection that returns successive batches of rows
    then an empty result to signal end-of-stream.

    rows_per_call: list of lists-of-dicts, one per execute() call.
    The last call always returns [] to terminate the pagination loop.
    """
    conn = MagicMock()
    call_results = []
    for batch in rows_per_call:
        result = MagicMock()
        result.mappings.return_value.all.return_value = batch
        call_results.append(result)
    # Final call returns empty list
    empty = MagicMock()
    empty.mappings.return_value.all.return_value = []
    call_results.append(empty)
    conn.execute.side_effect = call_results
    return conn


class TestExtractRecordMetadata:
    def test_yields_all_rows(self):
        batch1 = [
            {
                "record_id": 1,
                "record_num": 100,
                "record_type_code": "b",
                "creation_julianday": 2459000,
                "record_last_updated_julianday": 2459500,
                "deletion_julianday": None,
            },
        ]
        conn = _make_mock_conn([batch1])
        rows = list(extract.extract_record_metadata(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["record_type_code"] == "b"

    def test_paginates_on_last_id(self):
        batch1 = [
            {
                "record_id": 10,
                "record_num": 1,
                "record_type_code": "b",
                "creation_julianday": 2459000,
                "record_last_updated_julianday": 2459500,
                "deletion_julianday": None,
            },
            {
                "record_id": 20,
                "record_num": 2,
                "record_type_code": "i",
                "creation_julianday": 2459000,
                "record_last_updated_julianday": 2459500,
                "deletion_julianday": None,
            },
        ]
        conn = _make_mock_conn([batch1])
        rows = list(extract.extract_record_metadata(conn, itersize=2))
        assert len(rows) == 2
        # Second call should use id_val=20 (last row's record_id)
        second_call_kwargs = conn.execute.call_args_list[1][0][1]
        assert second_call_kwargs["id_val"] == 20

    def test_empty_result_yields_nothing(self):
        conn = _make_mock_conn([])
        rows = list(extract.extract_record_metadata(conn, itersize=1000))
        assert rows == []

    def test_multi_page_pagination(self):
        """Two full batches followed by an empty page yields all rows."""

        def _row(record_id):
            return {
                "record_id": record_id,
                "record_num": record_id,
                "record_type_code": "b",
                "creation_julianday": 2459000,
                "record_last_updated_julianday": 2459500,
                "deletion_julianday": None,
            }

        batch1 = [_row(1), _row(2)]
        batch2 = [_row(3), _row(4)]
        conn = _make_mock_conn([batch1, batch2])
        rows = list(extract.extract_record_metadata(conn, itersize=2))
        assert len(rows) == 4
        assert [r["record_id"] for r in rows] == [1, 2, 3, 4]
        # Third execute call should use cursor id from last row of batch2 (id=4)
        third_call_kwargs = conn.execute.call_args_list[2][0][1]
        assert third_call_kwargs["id_val"] == 4


class TestExtractBib:
    def test_yields_expected_columns(self):
        batch = [
            {
                "bib_record_num": 1001,
                "bib_record_id": 5000,
                "control_numbers": ["123"],
                "isbn_values": ["9780000000000"],
                "best_author": "Doe, Jane",
                "best_title": "A Test Book",
                "publisher": "Test Press",
                "publish_year": 2020,
                "bib_level_callnumber": "QA 123",
                "indexed_subjects": ["Fiction"],
                "genres": ["Novel"],
                "item_types": ["Book"],
                "cataloging_date": "2020-01-15",
            }
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_bib(conn, itersize=1000))
        assert len(rows) == 1
        row = rows[0]
        assert row["bib_record_num"] == 1001
        assert row["best_title"] == "A Test Book"
        assert row["best_author"] == "Doe, Jane"

    def test_paginates_using_bib_record_id(self):
        batch = [
            {
                "bib_record_num": 1,
                "bib_record_id": 42,
                "control_numbers": None,
                "isbn_values": None,
                "best_author": None,
                "best_title": "T",
                "publisher": None,
                "publish_year": None,
                "bib_level_callnumber": None,
                "indexed_subjects": None,
                "genres": None,
                "item_types": None,
                "cataloging_date": None,
            },
        ]
        conn = _make_mock_conn([batch])
        list(extract.extract_bib(conn, itersize=1))
        second_call_kwargs = conn.execute.call_args_list[1][0][1]
        assert second_call_kwargs["id_val"] == 42

    def test_single_row_last_page_terminates(self):
        """A single-row batch (< itersize) terminates after exactly 2 execute calls."""
        batch = [
            {
                "bib_record_num": 99,
                "bib_record_id": 99,
                "control_numbers": None,
                "isbn_values": None,
                "best_author": None,
                "best_title": "Single",
                "publisher": None,
                "publish_year": None,
                "bib_level_callnumber": None,
                "indexed_subjects": None,
                "genres": None,
                "item_types": None,
                "cataloging_date": None,
            }
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_bib(conn, itersize=10))
        assert len(rows) == 1
        # First call returns 1 row (< itersize=10), second call returns [] → stop
        assert conn.execute.call_count == 2


class TestExtractItem:
    def test_yields_expected_columns(self):
        batch = [
            {
                "item_record_num": 2001,
                "item_record_id": 6000,
                "bib_record_num": 1001,
                "creation_date": "2019-03-01",
                "record_last_updated": "2023-01-01",
                "barcode": "31068001234567",
                "agency_code_num": 0,
                "location_code": "2anf",
                "checkout_statistic_group_code_num": 10,
                "checkin_statistics_group_code_num": 10,
                "checkout_date": None,
                "due_date": None,
                "patron_branch_code": None,
                "last_checkout_date": "2022-06-15",
                "last_checkin_date": "2022-06-20",
                "checkout_total": 5,
                "renewal_total": 0,
                "item_format": "Book",
                "item_status_code": "-",
                "price_cents": 2499,
                "item_callnumber": "QA 123 .D63",
                "volume_record_num": None,
                "volume_record_statement": None,
            }
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_item(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["item_record_num"] == 2001
        assert rows[0]["item_status_code"] == "-"

    def test_paginates_using_item_record_id(self):
        batch = [
            {
                "item_record_num": 1,
                "item_record_id": 77,
                "bib_record_num": 1,
                "creation_date": None,
                "record_last_updated": None,
                "barcode": None,
                "agency_code_num": 0,
                "location_code": "x",
                "checkout_statistic_group_code_num": 0,
                "checkin_statistics_group_code_num": 0,
                "checkout_date": None,
                "due_date": None,
                "patron_branch_code": None,
                "last_checkout_date": None,
                "last_checkin_date": None,
                "checkout_total": 0,
                "renewal_total": 0,
                "item_format": None,
                "item_status_code": "-",
                "price_cents": 0,
                "item_callnumber": None,
                "volume_record_num": None,
                "volume_record_statement": None,
            },
        ]
        conn = _make_mock_conn([batch])
        list(extract.extract_item(conn, itersize=1))
        second_call_kwargs = conn.execute.call_args_list[1][0][1]
        assert second_call_kwargs["id_val"] == 77


class TestExtractBibRecord:
    def test_yields_expected_columns(self):
        batch = [
            {
                "id": 100,
                "record_id": 200,
                "language_code": "eng",
                "bcode1": "a",
                "bcode2": " ",
                "bcode3": "-",
                "country_code": "ohu",
                "index_change_count": 0,
                "is_on_course_reserve": False,
                "is_right_result_exact": True,
                "allocation_rule_code": " ",
                "skip_num": 0,
                "cataloging_date_gmt": "2020-01-15",
                "marc_type_code": "a",
                "is_suppressed": False,
            },
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_bib_record(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["language_code"] == "eng"


class TestExtractVolumeRecord:
    def test_yields_expected_columns(self):
        batch = [
            {
                "volume_record_id": 300,
                "volume_record_num": 10,
                "bib_record_id": 200,
                "bib_record_num": 1001,
                "creation_julianday": 2459000,
                "volume_statement": "v.1",
            },
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_volume_record(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["volume_statement"] == "v.1"


class TestExtractHold:
    def test_yields_expected_columns(self):
        batch = [
            {
                "hold_id": 1,
                "bib_record_num": 1001,
                "campus_code": "",
                "record_type_on_hold": "b",
                "item_record_num": None,
                "volume_record_num": None,
                "placed_julianday": 2459000,
                "is_frozen": False,
                "delay_days": 0,
                "location_code": "2anf",
                "expires_julianday": 2460000,
                "hold_status": "on hold",
                "is_ir": False,
                "is_ill": False,
                "pickup_location_code": "2anf",
                "ir_pickup_location_code": None,
                "ir_print_name": None,
                "ir_delivery_stop_name": None,
                "is_ir_converted_request": False,
                "patron_is_active": True,
                "patron_ptype_code": 0,
                "patron_home_library_code": "2anf",
                "patron_mblock_code": " ",
                "patron_has_over_10usd_owed": False,
            },
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_hold(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["hold_status"] == "on hold"


class TestExtractLookupTables:
    """Smoke tests for non-paginated lookup table extractors."""

    def _single_result_conn(self, rows):
        conn = MagicMock()
        result = MagicMock()
        result.mappings.return_value.all.return_value = rows
        conn.execute.return_value = result
        return conn

    def test_extract_language_property(self):
        rows = [{"id": 1, "code": "eng", "display_order": 1, "name": "English"}]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_language_property(conn))
        assert len(result) == 1
        assert result[0]["code"] == "eng"

    def test_extract_itype_property(self):
        rows = [
            {
                "itype_code": "0",
                "display_order": 1,
                "itype_name": "Book",
                "physical_format_name": "Print",
            }
        ]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_itype_property(conn))
        assert len(result) == 1
        assert result[0]["itype_name"] == "Book"

    def test_extract_item_status_property(self):
        rows = [{"item_status_code": "-", "display_order": 1, "item_status_name": "Available"}]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_item_status_property(conn))
        assert len(result) == 1
        assert result[0]["item_status_name"] == "Available"

    def test_extract_location(self):
        rows = [
            {
                "id": 1,
                "code": "2anf",
                "branch_code_num": 2,
                "parent_location_code": None,
                "is_public": True,
                "is_requestable": True,
            }
        ]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_location(conn))
        assert len(result) == 1
        assert result[0]["code"] == "2anf"

    def test_extract_branch_name(self):
        rows = [{"branch_id": 2, "name": "Anderson"}]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_branch_name(conn))
        assert len(result) == 1
        assert result[0]["name"] == "Anderson"

    def test_extract_location_name(self):
        rows = [{"location_id": 1, "name": "Main Library"}]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_location_name(conn))
        assert len(result) == 1
        assert result[0]["name"] == "Main Library"

    def test_extract_branch(self):
        rows = [
            {
                "id": 2,
                "address": "123 Main St",
                "email_source": None,
                "email_reply_to": None,
                "address_latitude": 39.1,
                "address_longitude": -84.5,
                "code_num": 2,
            }
        ]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_branch(conn))
        assert len(result) == 1
        assert result[0]["code_num"] == 2

    def test_extract_country_property_myuser(self):
        rows = [{"code": "ohu", "display_order": 1, "name": "Ohio"}]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_country_property_myuser(conn))
        assert len(result) == 1
        assert result[0]["code"] == "ohu"

    def test_extract_bib_level_property(self):
        rows = [
            {
                "bib_level_property_code": "a",
                "display_order": 1,
                "bib_level_property_name": "Monograph",
            }
        ]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_bib_level_property(conn))
        assert len(result) == 1
        assert result[0]["bib_level_property_code"] == "a"

    def test_extract_material_property(self):
        rows = [
            {
                "material_property_code": "a",
                "display_order": 1,
                "is_public": True,
                "material_property_name": "Book",
            }
        ]
        conn = self._single_result_conn(rows)
        result = list(extract.extract_material_property(conn))
        assert len(result) == 1
        assert result[0]["material_property_name"] == "Book"


class TestExtractCircAgg:
    def test_yields_rows(self):
        rows = [
            {
                "transaction_day": "2024-01-01",
                "stat_group_code_num": 10,
                "op_code": "o",
                "itype_code_num": 0,
                "loanrule_code_num": 1,
                "count_op_code": 42,
                "count_distinct_patrons": 30,
                "stat_group_name": "Anderson",
                "branch_code_num": 2,
                "branch_name": "Anderson",
            },
        ]
        conn = MagicMock()
        result = MagicMock()
        result.mappings.return_value.all.return_value = rows
        conn.execute.return_value = result
        result = list(extract.extract_circ_agg(conn))
        assert len(result) == 1
        assert result[0]["op_code"] == "o"


class TestExtractItemMessage:
    def test_yields_expected_columns(self):
        batch = [
            {
                "item_barcode": "31068012345678",
                "campus_code": "",
                "call_number": "FIC DOE",
                "item_record_id": 6001,
                "varfield_id": 9001,
                "has_in_transit": False,
                "in_transit_julianday": None,
                "in_transit_days": None,
                "transit_from": None,
                "transit_to": None,
                "has_in_transit_too_long": False,
                "occ_num": 0,
                "field_content": "some message",
                "publish_year": 2020,
                "best_title": "Test Book",
                "best_author": "Doe",
                "item_status_code": "-",
                "item_status_name": "Available",
                "agency_code_num": 0,
                "location_code": "2anf",
                "itype_code_num": 0,
                "item_format": "Book",
                "due_julianday": None,
                "loanrule_code_num": None,
                "checkout_julianday": None,
                "renewal_count": None,
                "overdue_count": None,
                "overdue_julianday": None,
            }
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_item_message(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["varfield_id"] == 9001
        assert rows[0]["item_status_code"] == "-"


class TestExtractBibRecordItemRecordLink:
    def test_yields_expected_columns(self):
        batch = [
            {
                "id": 1001,
                "bib_record_id": 5001,
                "bib_record_num": 1001,
                "item_record_id": 6001,
                "item_record_num": 2001,
                "items_display_order": 0,
                "bibs_display_order": 0,
            }
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_bib_record_item_record_link(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["bib_record_num"] == 1001
        assert rows[0]["item_record_num"] == 2001


class TestExtractVolumeRecordItemRecordLink:
    def test_yields_expected_columns(self):
        batch = [
            {
                "id": 2001,
                "volume_record_id": 3001,
                "volume_record_num": 10,
                "item_record_id": 6001,
                "item_record_num": 2001,
                "items_display_order": 0,
                "volume_statement": "v.1",
            }
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_volume_record_item_record_link(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["volume_statement"] == "v.1"


class TestExtractCircLeasedItems:
    def test_yields_expected_columns(self):
        batch = [
            {
                "id": 3001,
                "transaction_day": "2024-01-01",
                "stat_group_code_num": 10,
                "stat_group_name": "Anderson",
                "stat_group_location_code": "2anf",
                "stat_group_branch_name": "Anderson",
                "op_code": "o",
                "application_name": "Self-Checkout",
                "due_date": "2024-01-15",
                "item_record_id": 6001,
                "item_record_num": 2001,
                "barcode": "L000000123456",
                "bib_record_id": 5001,
                "bib_record_num": 1001,
                "volume_record_id": None,
                "volume_record_num": None,
                "itype_code_num": 0,
                "item_location_code": "2anf",
                "ptype_code": 0,
                "patron_home_library_code": "2anf",
                "patron_agency_code_num": 0,
                "loanrule_code_num": 1,
            }
        ]
        conn = _make_mock_conn([batch])
        rows = list(extract.extract_circ_leased_items(conn, itersize=1000))
        assert len(rows) == 1
        assert rows[0]["op_code"] == "o"
        assert rows[0]["barcode"] == "L000000123456"
