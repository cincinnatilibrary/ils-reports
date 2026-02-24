"""Unit tests for collection_analysis.extract — uses mock PostgreSQL connections."""

from unittest.mock import MagicMock

from collection_analysis import extract


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
