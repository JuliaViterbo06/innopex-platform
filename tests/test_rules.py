import datetime as dt

import pytest

from app.rules import (
    BusinessRuleError, check_profit, check_single_master, is_email_allowed, next_tuesdays, requires_profit,
)


def test_lucro_obrigatorio_a_partir_do_measure():
    assert not requires_profit("Define")
    assert requires_profit("Measure") and requires_profit("Control")
    check_profit("Define", 0)
    with pytest.raises(BusinessRuleError):
        check_profit("Measure", 0)


def test_master_unico():
    check_single_master("Silvia Marsiglia")
    for bad in ("Ana, Bia", "Ana e Bia", "Ana; Bia", "Ana/Bia"):
        with pytest.raises(BusinessRuleError):
            check_single_master(bad)


def test_somente_gm_com():
    assert is_email_allowed("julia.viterbomoreira@gm.com", "gm.com")
    assert not is_email_allowed("julia@gmail.com", "gm.com")
    assert not is_email_allowed("julia@gm.com.br", "gm.com")


def test_proximas_tercas():
    days = next_tuesdays(3, dt.date(2026, 11, 25))  # quarta-feira
    assert days == [dt.date(2026, 12, 1), dt.date(2026, 12, 8), dt.date(2026, 12, 15)]
    assert all(d.weekday() == 1 for d in days)
