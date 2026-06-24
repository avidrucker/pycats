"""Unit tests for the authentic Brawl/PM knockback + hitstun formula (#40)."""
import pytest

from pycats.combat.knockback import knockback, hitstun_frames
from pycats.config import HITSTUN_FLOOR


def test_knockback_zero_percent_neutral_weight():
    # p=0, d=10, w=100 -> inner 0; (0*1.4)+18=18; *KBG/100(=1)=18; +BKB(30)=48
    assert knockback(0.0, 10.0, 100, base_knockback=30.0, knockback_growth=100.0) == pytest.approx(48.0)


def test_knockback_high_percent_neutral_weight():
    # p=100, d=10, w=100 -> (10+50)=60; *1.0*1.4=84; +18=102; *1=102; +30=132
    assert knockback(100.0, 10.0, 100, base_knockback=30.0, knockback_growth=100.0) == pytest.approx(132.0)


def test_heavier_target_takes_less_knockback():
    light = knockback(100.0, 10.0, 50, base_knockback=30.0, knockback_growth=100.0)
    neutral = knockback(100.0, 10.0, 100, base_knockback=30.0, knockback_growth=100.0)
    heavy = knockback(100.0, 10.0, 200, base_knockback=30.0, knockback_growth=100.0)
    assert light > neutral > heavy
    assert heavy == pytest.approx(104.0)   # 200/300=.6667; 60*.6667*1.4=56; +18=74; +30=104


def test_knockback_growth_scales_the_percent_term():
    # KBG=0 -> growth term vanishes, leaving just BKB
    assert knockback(100.0, 10.0, 100, base_knockback=30.0, knockback_growth=0.0) == pytest.approx(30.0)


def test_hitstun_is_floored_product():
    assert hitstun_frames(132.0) == 52      # floor(52.8)
    assert hitstun_frames(48.0) == 19       # floor(19.2)


def test_hitstun_never_below_floor():
    assert hitstun_frames(0.0) == HITSTUN_FLOOR
    assert hitstun_frames(0.5) == HITSTUN_FLOOR


def test_hitstun_monotonic_in_knockback():
    assert hitstun_frames(50.0) <= hitstun_frames(100.0) <= hitstun_frames(200.0)
