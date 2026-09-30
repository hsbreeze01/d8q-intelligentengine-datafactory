import scheduler


def test_ok_when_reason_ok_and_data_date_matches():
    out = 'czsc_scan: reason=ok data_date=2026-08-18'
    assert scheduler._is_czsc_scan_ok(out, '2026-08-18', 0) is True


def test_fail_when_data_date_mismatch():
    out = 'czsc_scan: reason=ok data_date=2026-08-14'
    assert scheduler._is_czsc_scan_ok(out, '2026-08-18', 0) is False


def test_fail_when_reason_not_ok():
    out = 'czsc_scan: reason=non_trading_day data_date=2026-08-18'
    assert scheduler._is_czsc_scan_ok(out, '2026-08-18', 0) is False


def test_fail_when_returncode_nonzero():
    out = 'czsc_scan: reason=ok data_date=2026-08-18'
    assert scheduler._is_czsc_scan_ok(out, '2026-08-18', 1) is False


def test_fail_when_no_marker():
    out = 'some random output'
    assert scheduler._is_czsc_scan_ok(out, '2026-08-18', 0) is False


# --- explicit signal_count marker parser ------------------------------------

def test_signal_count_parses_real_success_marker_not_year():
    out = ('scan started 2026-09-30\n'
           'czsc_scan: reason=ok data_date=2026-09-30 signal_count=31')
    assert scheduler._parse_czsc_signal_count(out) == 31


def test_signal_count_handles_multiple_numbers_without_taking_first():
    out = 'czsc_scan: reason=ok data_date=2026-09-30 signal_count=7'
    assert scheduler._parse_czsc_signal_count(out) == 7


def test_signal_count_is_none_for_failed_or_missing_marker():
    assert scheduler._parse_czsc_signal_count(
        'czsc_scan: reason=data_not_ready data_date=2026-09-30 signal_count=9') is None
    assert scheduler._parse_czsc_signal_count(
        'czsc_scan: reason=ok data_date=2026-09-30') is None
    assert scheduler._parse_czsc_signal_count(None) is None


def test_signal_count_rejects_similar_or_embedded_text():
    assert scheduler._parse_czsc_signal_count(
        'INFO czsc_scan: reason=ok data_date=2026-09-30 signal_count=12') is None
    assert scheduler._parse_czsc_signal_count(
        'czsc_scan: reason=ok data_date=2026-09-30 signal_count=12oops') is None
    assert scheduler._parse_czsc_signal_count(
        'czsc_scan: reason=okay data_date=2026-09-30 signal_count=12') is None


def test_signal_count_last_valid_marker_wins_deterministically():
    out = ('czsc_scan: reason=ok data_date=2026-09-29 signal_count=5\n'
           'noise signal count 2026\n'
           'czsc_scan: reason=ok data_date=2026-09-30 signal_count=31')
    assert scheduler._parse_czsc_signal_count(out) == 31
