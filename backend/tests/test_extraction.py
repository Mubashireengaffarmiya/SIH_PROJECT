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

    def test_decimal_kg(self):
        r = extract_net_quantity("Net Quantity: 0.5 kg", _words(["Net", "Quantity:", "0.5", "kg"]))
        assert r["value"] == "0.5 kg"

    def test_decimal_litre(self):
        r = extract_net_quantity("Net Quantity: 1.25 L", _words(["Net", "Quantity:", "1.25", "L"]))
        assert r["value"] == "1.25 l"

    def test_decimal_ml_preserves_decimal(self):
        r = extract_net_quantity("Net Quantity: 500.0 ml", _words(["Net", "Quantity:", "500.0", "ml"]))
        assert r["value"] == "500.0 ml"

    def test_supported_piece_unit(self):
        r = extract_net_quantity("Net Qty. 10 pieces", _words(["Net", "Qty.", "10", "pieces"]))
        assert r["value"] == "10 pieces"

    def test_ocr_numeric_confusion(self):
        r = extract_net_quantity("NET QUANT1TY 1009", _words(["NET", "QUANT1TY", "1009"]))
        assert r["value"] == "100 g"

    def test_ocr_letter_o_confusion(self):
        r = extract_net_quantity("NET WT O.5 kg", _words(["NET", "WT", "O.5", "kg"]))
        assert r["value"] == "0.5 kg"

    def test_comma_decimal(self):
        r = extract_net_quantity("NET WT 0,5 kg", _words(["NET", "WT", "0,5", "kg"]))
        assert r["value"] == "0.5 kg"

    def test_nutrition_quantity_is_not_selected(self):
        words = [
            {"text": "Protein", "confidence": 0.98, "bbox": [10, 10, 80, 30]},
            {"text": "6", "confidence": 0.98, "bbox": [90, 10, 105, 30]},
            {"text": "g", "confidence": 0.98, "bbox": [110, 10, 125, 30]},
            {"text": "NET", "confidence": 0.92, "bbox": [10, 100, 50, 120]},
            {"text": "QUANTITY", "confidence": 0.92, "bbox": [55, 100, 130, 120]},
            {"text": "100", "confidence": 0.92, "bbox": [140, 100, 175, 120]},
            {"text": "g", "confidence": 0.92, "bbox": [180, 100, 195, 120]},
        ]
        result = extract_net_quantity("Protein 6 g NET QUANTITY 100 g", words)
        assert result["value"] == "100 g"

    def test_explicit_label_without_value_does_not_use_distant_nutrition(self):
        words = [
            {"text": "NET", "confidence": 0.92, "bbox": [10, 100, 50, 120]},
            {"text": "QUANTITY", "confidence": 0.92, "bbox": [55, 100, 130, 120]},
            {"text": "Protein", "confidence": 0.98, "bbox": [10, 500, 80, 520]},
            {"text": "6", "confidence": 0.98, "bbox": [90, 500, 105, 520]},
            {"text": "g", "confidence": 0.98, "bbox": [110, 500, 125, 520]},
        ]
        result = extract_net_quantity("NET QUANTITY Protein 6 g", words)
        assert result["value"] is None


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

    def test_product_name_prevails_over_nutrition_table(self):
        words = [
            {"text": "ENERGY", "confidence": 0.91, "bbox": [10, 20, 120, 50]},
            {"text": "530", "confidence": 0.91, "bbox": [130, 20, 180, 50]},
            {"text": "kcal", "confidence": 0.91, "bbox": [190, 20, 250, 50]},
            {"text": "Lay's", "confidence": 0.94, "bbox": [20, 120, 140, 160]},
            {"text": "Classic", "confidence": 0.94, "bbox": [150, 120, 260, 160]},
            {"text": "Salted", "confidence": 0.94, "bbox": [270, 120, 390, 160]},
            {"text": "NET", "confidence": 0.92, "bbox": [20, 200, 100, 230]},
            {"text": "QUANTITY", "confidence": 0.92, "bbox": [110, 200, 260, 230]},
            {"text": "52", "confidence": 0.92, "bbox": [270, 200, 310, 230]},
            {"text": "g", "confidence": 0.92, "bbox": [320, 200, 340, 230]},
            {"text": "MRP", "confidence": 0.94, "bbox": [20, 260, 90, 290]},
            {"text": "₹20.00", "confidence": 0.94, "bbox": [100, 260, 190, 290]},
        ]
        result = extract_all({"full_text": "ENERGY 530 kcal Lay's Classic Salted NET QUANTITY 52 g MRP ₹20.00", "words": words})
        assert result["product_name"]["value"] == "Lay's Classic Salted"
        assert result["net_quantity"]["value"] == "52 g"
        assert result["mrp"]["value"] == "₹20.00"

    def test_net_quantity_ignores_nutrition_values(self):
        words = [
            {"text": "Energy", "confidence": 0.90, "bbox": [10, 10, 100, 36]},
            {"text": "530", "confidence": 0.90, "bbox": [110, 10, 150, 36]},
            {"text": "kcal", "confidence": 0.90, "bbox": [160, 10, 210, 36]},
            {"text": "NET", "confidence": 0.92, "bbox": [10, 120, 80, 150]},
            {"text": "QUANT1TY", "confidence": 0.92, "bbox": [90, 120, 220, 150]},
            {"text": "52", "confidence": 0.92, "bbox": [230, 120, 260, 150]},
            {"text": "g", "confidence": 0.92, "bbox": [270, 120, 290, 150]},
        ]
        result = extract_net_quantity("Energy 530 kcal NET QUANT1TY 52 g", words)
        assert result["value"] == "52 g"

    def test_manufacturer_value_from_keyword_cluster(self):
        words = [
            {"text": "Manufactured", "confidence": 0.93, "bbox": [10, 200, 120, 230]},
            {"text": "&", "confidence": 0.93, "bbox": [120, 200, 130, 230]},
            {"text": "Packed", "confidence": 0.93, "bbox": [130, 200, 210, 230]},
            {"text": "by:", "confidence": 0.93, "bbox": [210, 200, 250, 230]},
            {"text": "PEPSICO", "confidence": 0.92, "bbox": [10, 240, 120, 270]},
            {"text": "INDIA", "confidence": 0.92, "bbox": [130, 240, 220, 270]},
            {"text": "REGION", "confidence": 0.92, "bbox": [230, 240, 320, 270]},
            {"text": "Frito-Lay", "confidence": 0.91, "bbox": [10, 280, 130, 310]},
            {"text": "India", "confidence": 0.91, "bbox": [140, 280, 200, 310]},
            {"text": "(India)", "confidence": 0.91, "bbox": [210, 280, 290, 310]},
            {"text": "Pvt.", "confidence": 0.91, "bbox": [10, 320, 70, 350]},
            {"text": "Ltd.", "confidence": 0.91, "bbox": [80, 320, 130, 350]},
        ]
        result = extract_manufacturer("Manufactured & Packed by: PEPSICO INDIA REGION Frito-Lay India (India) Pvt. Ltd.", words)
        assert result["value"] is not None
        assert "PEPSICO" in result["value"]
        assert "Frito-Lay" in result["value"]

    def test_empty_ocr(self):
        ocr = {"full_text": "", "words": []}
        result = extract_all(ocr)
        for key in ["mrp", "net_quantity", "manufacturer", "manufacturing_date",
                    "consumer_care", "country_of_origin", "best_before"]:
            assert result[key]["value"] is None
