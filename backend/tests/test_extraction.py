"""
Tests for field extraction service.
Run: cd backend && pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.extraction import (
    extract_mrp,
    extract_net_quantity,
    extract_manufacturer,
    extract_manufacturing_date,
    extract_consumer_care,
    extract_country_of_origin,
    extract_best_before,
    extract_unit_sale_price,
    extract_product_name,
    extract_all,
)


def _words(texts):
    return [{"text": t, "confidence": 0.95, "bbox": [0, 0, 100, 20]} for t in texts]


# ---------------------------------------------------------------------------
# MRP
# ---------------------------------------------------------------------------

class TestMRP:
    def test_rupee_symbol(self):
        r = extract_mrp("MRP ₹50", _words(["MRP", "₹50"]))
        assert r["value"] == "₹50"

    def test_rs_dot(self):
        r = extract_mrp("MRP Rs.100", _words(["MRP", "Rs.100"]))
        assert r["value"] is not None
        assert "100" in r["value"]

    def test_maximum_retail_price(self):
        r = extract_mrp("Maximum Retail Price ₹250.00", _words(["Maximum", "Retail", "Price", "₹250.00"]))
        assert r["value"] is not None

    def test_not_found(self):
        r = extract_mrp("Net Qty 500g Manufacturer XYZ", _words(["Net", "Qty", "500g"]))
        assert r["value"] is None
        assert r["confidence"] == "LOW"

    def test_inr_keyword(self):
        r = extract_mrp("MRP INR 75", _words(["MRP", "INR", "75"]))
        assert r["value"] is not None


# ---------------------------------------------------------------------------
# Net Quantity
# ---------------------------------------------------------------------------

class TestNetQuantity:
    def test_grams(self):
        r = extract_net_quantity("Net Qty: 100g", _words(["Net", "Qty:", "100g"]))
        assert r["value"] is not None
        assert "100" in r["value"]

    def test_ml(self):
        r = extract_net_quantity("Net Quantity: 500 ml", _words(["Net", "Quantity:", "500", "ml"]))
        assert r["value"] is not None

    def test_litre(self):
        r = extract_net_quantity("Net Vol. 1 L", _words(["Net", "Vol.", "1", "L"]))
        assert r["value"] is not None

    def test_kg(self):
        r = extract_net_quantity("Net Weight: 5 kg", _words(["Net", "Weight:", "5", "kg"]))
        assert r["value"] is not None

    def test_standalone(self):
        r = extract_net_quantity("250g best quality", _words(["250g", "best", "quality"]))
        assert r["value"] is not None

    def test_not_found(self):
        r = extract_net_quantity("MRP ₹50 Manufacturer XYZ", _words(["MRP", "₹50"]))
        assert r["value"] is None


# ---------------------------------------------------------------------------
# Manufacturer
# ---------------------------------------------------------------------------

class TestManufacturer:
    def test_manufactured_by(self):
        r = extract_manufacturer("Manufactured by: ABC Foods Pvt. Ltd. Mumbai", _words([
            "Manufactured", "by:", "ABC", "Foods", "Pvt.", "Ltd.", "Mumbai"
        ]))
        assert r["value"] is not None
        assert "ABC" in r["value"]

    def test_packed_by(self):
        r = extract_manufacturer("Packed by XYZ Company, Delhi", _words(["Packed", "by", "XYZ"]))
        assert r["value"] is not None

    def test_imported_by(self):
        r = extract_manufacturer("Imported by International Traders, Chennai", _words(
            ["Imported", "by", "International", "Traders", "Chennai"]
        ))
        assert r["value"] is not None

    def test_not_found(self):
        r = extract_manufacturer("MRP ₹50 Net Qty 100g", _words(["MRP", "₹50"]))
        assert r["value"] is None


# ---------------------------------------------------------------------------
# Manufacturing Date
# ---------------------------------------------------------------------------

class TestManufacturingDate:
    def test_mfd_slash(self):
        r = extract_manufacturing_date("MFD: 09/2026", _words(["MFD:", "09/2026"]))
        assert r["value"] == "09/2026"

    def test_mfg_date(self):
        r = extract_manufacturing_date("Mfg Date: Aug 2026", _words(["Mfg", "Date:", "Aug", "2026"]))
        assert r["value"] is not None

    def test_manufactured_on(self):
        r = extract_manufacturing_date("Manufactured on: January 2026", _words(
            ["Manufactured", "on:", "January", "2026"]
        ))
        assert r["value"] is not None

    def test_not_found(self):
        r = extract_manufacturing_date("MRP ₹50 Net Qty 100g", _words(["MRP", "₹50"]))
        assert r["value"] is None


# ---------------------------------------------------------------------------
# Consumer Care
# ---------------------------------------------------------------------------

class TestConsumerCare:
    def test_phone_10_digit(self):
        r = extract_consumer_care("Consumer Care: 9876543210", _words(["Consumer", "Care:", "9876543210"]))
        assert r["value"] is not None

    def test_toll_free(self):
        r = extract_consumer_care("Toll Free: 1800 123 4567", _words(["Toll", "Free:", "1800", "123", "4567"]))
        assert r["value"] is not None

    def test_email(self):
        r = extract_consumer_care("care@example.com", _words(["care@example.com"]))
        assert r["value"] is not None
        assert "@" in r["value"]

    def test_not_found(self):
        r = extract_consumer_care("MRP ₹50 Net Qty 100g", _words(["MRP", "₹50"]))
        assert r["value"] is None


# ---------------------------------------------------------------------------
# Country of Origin
# ---------------------------------------------------------------------------

class TestCountryOfOrigin:
    def test_country_of_origin(self):
        r = extract_country_of_origin("Country of Origin: India", _words(["Country", "of", "Origin:", "India"]))
        assert r["value"] is not None
        assert "India" in r["value"]

    def test_made_in(self):
        r = extract_country_of_origin("Made in Nepal", _words(["Made", "in", "Nepal"]))
        assert r["value"] is not None
        assert "Nepal" in r["value"]

    def test_not_found(self):
        r = extract_country_of_origin("MRP ₹50 Net Qty 100g", _words(["MRP", "₹50"]))
        assert r["value"] is None


# ---------------------------------------------------------------------------
# Best Before
# ---------------------------------------------------------------------------

class TestBestBefore:
    def test_best_before_date(self):
        r = extract_best_before("Best Before: 12/2027", _words(["Best", "Before:", "12/2027"]))
        assert r["value"] is not None

    def test_expiry(self):
        r = extract_best_before("Exp. Date: Jan 2028", _words(["Exp.", "Date:", "Jan", "2028"]))
        assert r["value"] is not None

    def test_use_by(self):
        r = extract_best_before("Use By: 03/2027", _words(["Use", "By:", "03/2027"]))
        assert r["value"] is not None

    def test_months_from_mfg(self):
        r = extract_best_before("Best Before: 12 months from mfg date", _words(
            ["Best", "Before:", "12", "months", "from", "mfg", "date"]
        ))
        assert r["value"] is not None

    def test_not_found(self):
        r = extract_best_before("MRP ₹50 Net Qty 100g", _words(["MRP", "₹50"]))
        assert r["value"] is None


# ---------------------------------------------------------------------------
# extract_all integration
# ---------------------------------------------------------------------------

class TestExtractAll:
    def test_complete_ocr_result(self):
        ocr = {
            "full_text": (
                "SUNRISE ATTA Net Qty: 5 kg MRP ₹250.00 "
                "Manufactured by: Sunrise Foods Pvt Ltd Mumbai "
                "MFD: 09/2026 Best Before: 09/2027 "
                "Country of Origin: India Consumer Care: 1800-123-4567"
            ),
            "words": _words([
                "SUNRISE", "ATTA", "Net", "Qty:", "5", "kg",
                "MRP", "₹250.00", "Manufactured", "by:", "Sunrise", "Foods",
                "Pvt", "Ltd", "Mumbai", "MFD:", "09/2026", "Best", "Before:",
                "09/2027", "Country", "of", "Origin:", "India",
                "Consumer", "Care:", "1800-123-4567"
            ]),
        }
        result = extract_all(ocr)
        assert result["mrp"]["value"] is not None
        assert "250" in result["mrp"]["value"]
        assert result["net_quantity"]["value"] is not None
        assert result["manufacturer"]["value"] is not None
        assert result["manufacturing_date"]["value"] is not None
        assert result["best_before"]["value"] is not None
        assert result["country_of_origin"]["value"] is not None
        assert result["consumer_care"]["value"] is not None

    def test_empty_ocr(self):
        ocr = {"full_text": "", "words": []}
        result = extract_all(ocr)
        for key in ["mrp", "net_quantity", "manufacturer", "manufacturing_date",
                    "consumer_care", "country_of_origin", "best_before"]:
            assert result[key]["value"] is None
