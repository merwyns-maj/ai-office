import colorsys
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.runtime import providers
from tests._helpers import REPO

OFFICE = REPO / "offices/ai-office"
TEST_CFG = REPO / "tests/fixtures/providers-test.yaml"


def good():
    return {
        "plan-p": {"billing": "plan", "code": "PLN", "colour": "#c084fc", "models": {"m": {"short": "m"}}},
        "tok-p": {"billing": "per_token", "code": "TOK", "colour": "#5b8def", "prices": {"source": None, "checked": None},
                  "models": {"m": {"short": "m", "input": None, "output": None, "cache_read": None, "cache_write": None}}},
    }


def with_root(text):
    tmp = tempfile.TemporaryDirectory()
    Path(tmp.name, providers.FILE).write_text(text, encoding="utf-8")
    return tmp


class Loading(unittest.TestCase):
    def test_repo_config_loads_clean_with_four_providers(self):
        cat, probs = providers.load_providers(OFFICE)
        self.assertEqual(probs, [])
        self.assertEqual(sorted(cat), ["anthropic-api", "claude-code", "claude-sdk", "deepseek", "openai"])
        self.assertEqual(cat["claude-sdk"]["billing"], "plan")

    def test_repo_config_has_no_price_set(self):
        # Prices stay null until someone fills one from a provider page with a dated source (T-056 approvals).
        cat, _ = providers.load_providers(OFFICE)
        for pid, p in cat.items():
            for mid, m in p["models"].items():
                for k in providers.PRICE_KEYS:
                    self.assertIsNone(m.get(k), f"{pid}/{mid}/{k}")

    def test_test_config_loads_and_has_dated_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(TEST_CFG, Path(tmp) / providers.FILE)
            cat, probs = providers.load_providers(tmp)
        self.assertEqual(probs, [])
        self.assertEqual(cat["token-test"]["models"]["tok-model"]["cache_read"], 0.0625)

    def test_no_file_is_empty_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(providers.load_providers(tmp), ({}, []))

    def test_bad_yaml_and_wrong_shape_are_problems(self):
        for text in ("providers: [1, 2]\n", "other: 1\n", "providers:\n  a: {\n"):
            tmp = with_root(text)
            cat, probs = providers.load_providers(tmp.name)
            self.assertEqual(cat, {})
            self.assertEqual(len(probs), 1, text)
            tmp.cleanup()


class Rules(unittest.TestCase):
    def one(self, mutate, text):
        d = good()
        mutate(d)
        probs = providers.validate(d)
        self.assertTrue(any(text in p for p in probs), (text, probs))

    def test_good_catalogue_passes(self):
        self.assertEqual(providers.validate(good()), [])

    def test_each_rule_rejects(self):
        self.one(lambda d: d["tok-p"].update(billing="free"), "billing")
        self.one(lambda d: d["tok-p"].update(code="toolong"), "code")
        self.one(lambda d: d["tok-p"].update(code="a"), "code")
        self.one(lambda d: d["tok-p"].update(colour="purple"), "colour")
        self.one(lambda d: d["tok-p"].update(colour="#fff"), "colour")
        self.one(lambda d: d["tok-p"]["models"]["m"].update(short="x" * 13), "short")
        self.one(lambda d: d["tok-p"]["models"]["m"].pop("short"), "short")
        self.one(lambda d: d["tok-p"].update(models={}), "models")

    def test_plan_provider_must_not_have_prices(self):
        self.one(lambda d: d["plan-p"].update(prices={"source": "x", "checked": "2026-01-01"}), "plan provider must not have prices")
        self.one(lambda d: d["plan-p"]["models"]["m"].update(input=1), "must not have price")

    def test_price_must_be_null_or_bounded_number_with_four_decimals(self):
        for bad in (-1, 10001, 0.12345, "3", True):
            def m(d, bad=bad):
                d["tok-p"]["models"]["m"]["input"] = bad
            self.one(m, "price input")
        for ok in (0, 0.0001, 10000, 3.5):
            d = good()
            d["tok-p"]["models"]["m"]["input"] = ok
            d["tok-p"]["prices"] = {"source": "page", "checked": "2026-11-26"}
            self.assertEqual(providers.validate(d), [], ok)

    def test_a_price_without_a_dated_source_fails(self):
        for prices in ({"source": None, "checked": None}, {"source": "page", "checked": None}, {"source": None, "checked": "2026-11-26"},
                       {"source": "page", "checked": "26/11/2026"}, {"source": "page", "checked": "2026-13-40"}, None):
            d = good()
            d["tok-p"]["models"]["m"]["input"] = 3
            d["tok-p"]["prices"] = prices
            probs = providers.validate(d)
            self.assertTrue(any("source or prices.checked" in p for p in probs), (prices, probs))


def hue(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


class Palette(unittest.TestCase):
    def test_provider_colours_avoid_amber_red_and_the_accent(self):
        cat, _ = providers.load_providers(OFFICE)
        theme = (OFFICE / "theme/theme.yaml").read_text(encoding="utf-8")
        accent = re.search(r'accent:\s*"(#[0-9a-fA-F]{6})"', theme).group(1)
        for pid, p in cat.items():
            h = hue(p["colour"])
            self.assertFalse(h <= 45 or h >= 345, f"{pid} hue {h:.0f} is amber or red")
            d = abs(h - hue(accent))
            self.assertGreater(min(d, 360 - d), 15, f"{pid} hue {h:.0f} is close to the accent")

    def test_codes_and_colours_are_distinct(self):
        cat, _ = providers.load_providers(OFFICE)
        self.assertEqual(len({p["code"] for p in cat.values()}), len(cat))
        self.assertEqual(len({p["colour"] for p in cat.values()}), len(cat))


if __name__ == "__main__":
    unittest.main()
