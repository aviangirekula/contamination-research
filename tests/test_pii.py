"""Tests for the regex PII detectors. Uses ONLY synthetic strings (no real PII)."""
from extraction.pii import find_pii, pii_types


def test_email_detected():
    assert pii_types("contact a@b.com please") == {"email"}
    spans = find_pii("x a@b.com y")
    assert len(spans) == 1
    t, (s, e) = spans[0]
    assert t == "email"
    assert "x a@b.com y"[s:e] == "a@b.com"


def test_email_variants():
    assert pii_types("first.last+tag@sub.example.org") == {"email"}
    # no TLD -> not an email
    assert pii_types("nope@localhost") == set()


def test_phone_formats():
    assert pii_types("call 555-123-4567 now") == {"phone"}
    assert pii_types("call (555) 123-4567 now") == {"phone"}
    assert pii_types("call 555.123.4567 now") == {"phone"}
    assert pii_types("call +1 555 123 4567 now") == {"phone"}


def test_phone_span_exact():
    spans = find_pii("ph 555-123-4567 end")
    phones = [s for s in spans if s[0] == "phone"]
    assert len(phones) == 1
    _, (s, e) = phones[0]
    assert "ph 555-123-4567 end"[s:e] == "555-123-4567"


def test_ssn_detected_and_not_phone():
    types = pii_types("ssn 123-45-6789 here")
    assert "ssn" in types
    assert "phone" not in types


def test_no_pii():
    assert pii_types("just plain words, no identifiers 2026") == set()
    assert find_pii("") == []


def test_multiple_types():
    text = "mail a@b.com or call 555-123-4567"
    assert pii_types(text) == {"email", "phone"}
    assert len(find_pii(text)) == 2


def test_spans_sorted():
    text = "555-123-4567 then a@b.com"
    spans = find_pii(text)
    starts = [span[1][0] for span in spans]
    assert starts == sorted(starts)
