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
