"""SplitMix64 gegen die veröffentlichten Referenzwerte (Vigna, Seed 0) und Grundeigenschaften von below()."""
import abl_rng


def test_splitmix64_reference_values_for_seed_zero():
    r = abl_rng.SplitMix64(0)
    assert [r.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]


def test_below_stays_in_range_and_is_roughly_uniform():
    r = abl_rng.SplitMix64(12345)
    draws = [r.below(6) for _ in range(6000)]
    assert set(draws) == set(range(6))
    assert all(abs(draws.count(i) - 1000) < 120 for i in range(6))
    assert abl_rng.SplitMix64(1).randrange(10) == abl_rng.SplitMix64(1).below(10)
