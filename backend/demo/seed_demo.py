"""
SMART-LM Demo Data Seeder
==========================
Generates synthetic product label images and seeds demo inspections into the database.

Run from the backend/ directory:
    python demo/seed_demo.py

IMPORTANT: All data generated here is SYNTHETIC / DEMO DATA.
It is NOT real enforcement evidence and must never be used as such.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
import random

# Add backend dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from database.database import init_db, SessionLocal, Inspection, Declaration, Violation, User
from routers.auth import get_password_hash

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "test_images")
os.makedirs(DEMO_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Label templates
# ---------------------------------------------------------------------------

LABEL_TEMPLATES = [
    {
        "name": "good_label",
        "scenario": "Complete label — all declarations present",
        "lines": [
            ("SUNRISE ATTA", 28, True),
            ("Whole Wheat Flour", 16, False),
            ("", 10, False),
            ("Net Qty: 5 kg", 14, False),
            ("MRP ₹ 250.00 (Incl. of all taxes)", 14, False),
            ("", 10, False),
            ("Manufactured by: Sunrise Food Products Pvt. Ltd.", 11, False),
            ("Plot No. 42, Industrial Area, Pune - 411 001", 10, False),
            ("FSSAI Lic. No.: 10019022003744", 10, False),
            ("", 8, False),
            ("MFD: 09/2026  Best Before: 09/2027", 11, False),
            ("Country of Origin: India", 11, False),
            ("Consumer Care: 1800-123-4567 | care@sunrise.in", 10, False),
        ],
        "bg_color": (255, 248, 220),
        "text_color": (30, 30, 30),
        "accent": (180, 100, 0),
        "quality": "good",
    },
    {
        "name": "missing_mrp",
        "scenario": "Missing MRP — potential compliance issue",
        "lines": [
            ("FRESH DAILY BISCUITS", 26, True),
            ("Butter Cookies — 200g", 14, False),
            ("", 10, False),
            ("Manufactured by: Fresh Bake Industries", 11, False),
            ("Sector 5, Noida - 201301", 10, False),
            ("", 8, False),
            ("Mfd: Aug 2026", 11, False),
            ("Best Before: 6 months from mfg date", 11, False),
            ("Country of Origin: India", 11, False),
            ("Consumer Care: 011-2345-6789", 10, False),
            # MRP intentionally missing
        ],
        "bg_color": (240, 255, 240),
        "text_color": (20, 60, 20),
        "accent": (0, 120, 50),
        "quality": "good",
    },
    {
        "name": "blurry_label",
        "scenario": "Blurry image — OCR unreliable",
        "lines": [
            ("GOLDEN RICE BASMATI", 28, True),
            ("Premium Long Grain Rice", 16, False),
            ("Net Qty: 2 kg", 14, False),
            ("MRP ₹ 180.00", 14, False),
            ("Packed by: Golden Grain Co., Mumbai", 11, False),
            ("MFD: Jul 2026 | Best Before: Jul 2027", 11, False),
            ("Country of Origin: India", 11, False),
            ("Consumer Care: 022-9876-5432", 10, False),
        ],
        "bg_color": (255, 250, 230),
        "text_color": (40, 30, 10),
        "accent": (180, 140, 0),
        "quality": "blurry",
    },
    {
        "name": "dark_image",
        "scenario": "Poorly lit image — low brightness",
        "lines": [
            ("NATURE PURE HONEY", 26, True),
            ("100% Natural — 500g", 14, False),
            ("MRP ₹ 320.00 (Incl. taxes)", 14, False),
            ("Imported by: Nature Foods Ltd.", 11, False),
            ("22, Park Street, Kolkata - 700 016", 10, False),
            ("Country of Origin: Nepal", 11, False),
            ("Best Before: 2 years from manufacture", 11, False),
            ("Consumer Care: info@naturepure.in", 10, False),
        ],
        "bg_color": (200, 180, 120),
        "text_color": (20, 10, 0),
        "accent": (100, 60, 0),
        "quality": "dark",
    },
    {
        "name": "angled_label",
        "scenario": "Angled photograph — some text distorted",
        "lines": [
            ("VITACARE VITAMIN C TABLETS", 22, True),
            ("500mg — 60 Tablets", 14, False),
            ("Net Qty: 60 tabs", 14, False),
            ("MRP ₹ 199.00", 14, False),
            ("Manufactured by: VitaCare Pharma, Hyderabad", 11, False),
            ("Mfg Date: June 2026 | Expiry: May 2028", 11, False),
            ("Country of Origin: India", 11, False),
            ("Consumer Care: 040-1234-5678", 10, False),
        ],
        "bg_color": (220, 235, 255),
        "text_color": (10, 30, 80),
        "accent": (30, 80, 200),
        "quality": "angled",
    },
]


def create_label_image(template: dict, output_path: str):
    """Generate a synthetic product label image."""
    width, height = 500, 400
    img = Image.new("RGB", (width, height), template["bg_color"])
    draw = ImageDraw.Draw(img)

    # Background decoration
    draw.rectangle([0, 0, width, 50], fill=template["accent"])
    draw.rectangle([0, height - 30, width, height], fill=template["accent"])

    # DEMO watermark band
    draw.rectangle([0, height - 65, width, height - 35], fill=(255, 200, 0, 128))

    # Try to use a system font, fall back to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 28)
        font_medium = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 11)
        font_tiny = ImageFont.truetype("arial.ttf", 10)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
        font_tiny = font_large

    y = 60
    for text, size, bold in template["lines"]:
        if not text:
            y += size
            continue
        try:
            if size >= 22:
                font = font_large
            elif size >= 13:
                font = font_medium
            elif size >= 11:
                font = font_small
            else:
                font = font_tiny
        except Exception:
            font = ImageFont.load_default()

        color = template["accent"] if bold else template["text_color"]
        draw.text((20, y), text, fill=color, font=font)
        y += size + 6

    # DEMO watermark
    draw.text((10, height - 62), "★ DEMO DATA — NOT REAL ENFORCEMENT EVIDENCE ★",
              fill=(150, 0, 0), font=font_tiny)

    # Apply quality effects
    if template["quality"] == "blurry":
        img = img.filter(ImageFilter.GaussianBlur(radius=4))
    elif template["quality"] == "dark":
        img = img.point(lambda p: p * 0.35)
    elif template["quality"] == "angled":
        # Simulate perspective by applying affine-like crop/paste
        img = img.rotate(12, fillcolor=(200, 200, 200), expand=False)

    img.save(output_path, "JPEG", quality=85)
    print(f"  Created: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Database seeding
# ---------------------------------------------------------------------------

DEMO_INSPECTIONS = [
    {
        "product_name": "Sunrise Atta (Whole Wheat Flour)",
        "status": "VERIFIED_COMPLIANT",
        "overall_confidence": "HIGH",
        "image_quality": "GOOD",
        "template_name": "good_label",
        "declarations": [
            ("product_name", "Sunrise Atta", "HIGH", "VERIFIED_COMPLIANT"),
            ("mrp", "₹250.00", "HIGH", "VERIFIED_COMPLIANT"),
            ("net_quantity", "5 kg", "HIGH", "VERIFIED_COMPLIANT"),
            ("manufacturer", "Sunrise Food Products Pvt. Ltd.", "HIGH", "VERIFIED_COMPLIANT"),
            ("manufacturing_date", "09/2026", "HIGH", "VERIFIED_COMPLIANT"),
            ("consumer_care", "1800-123-4567", "HIGH", "VERIFIED_COMPLIANT"),
            ("country_of_origin", "India", "HIGH", "VERIFIED_COMPLIANT"),
            ("best_before", "09/2027", "HIGH", "VERIFIED_COMPLIANT"),
        ],
        "violations": [],
    },
    {
        "product_name": "Fresh Daily Biscuits (Butter Cookies)",
        "status": "NEEDS_HUMAN_REVIEW",
        "overall_confidence": "MEDIUM",
        "image_quality": "GOOD",
        "template_name": "missing_mrp",
        "declarations": [
            ("product_name", "Fresh Daily Biscuits", "HIGH", "VERIFIED_COMPLIANT"),
            ("mrp", None, "LOW", "NEEDS_HUMAN_REVIEW"),
            ("net_quantity", "200g", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("manufacturer", "Fresh Bake Industries", "HIGH", "VERIFIED_COMPLIANT"),
            ("manufacturing_date", "Aug 2026", "HIGH", "VERIFIED_COMPLIANT"),
            ("consumer_care", "011-2345-6789", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("country_of_origin", "India", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("best_before", "6 months from mfg date", "MEDIUM", "VERIFIED_COMPLIANT"),
        ],
        "violations": [
            {
                "field_name": "mrp",
                "reason": (
                    "'MRP declaration' was not confidently detected in the image. "
                    "This may be due to image quality, OCR limitations, or the declaration may be absent. "
                    "Human review required."
                ),
                "severity": "HIGH",
                "confidence": "LOW",
                "rule_id": "PC-MRP-001",
            }
        ],
    },
    {
        "product_name": "Golden Basmati Rice",
        "status": "NEEDS_HUMAN_REVIEW",
        "overall_confidence": "LOW",
        "image_quality": "POOR",
        "template_name": "blurry_label",
        "declarations": [
            ("product_name", None, "LOW", "NEEDS_HUMAN_REVIEW"),
            ("mrp", None, "LOW", "NEEDS_HUMAN_REVIEW"),
            ("net_quantity", None, "LOW", "NEEDS_HUMAN_REVIEW"),
            ("manufacturer", None, "LOW", "NEEDS_HUMAN_REVIEW"),
            ("manufacturing_date", None, "LOW", "NEEDS_HUMAN_REVIEW"),
            ("consumer_care", None, "LOW", "NEEDS_HUMAN_REVIEW"),
        ],
        "violations": [
            {
                "field_name": "general",
                "reason": "Image quality is POOR (blurry). OCR results are unreliable. Please retake the photograph.",
                "severity": "HIGH",
                "confidence": "LOW",
                "rule_id": None,
            }
        ],
    },
    {
        "product_name": "Nature Pure Honey",
        "status": "NEEDS_HUMAN_REVIEW",
        "overall_confidence": "LOW",
        "image_quality": "POOR",
        "template_name": "dark_image",
        "declarations": [
            ("product_name", "Nature Pure Honey", "LOW", "NEEDS_HUMAN_REVIEW"),
            ("mrp", "₹320.00", "LOW", "NEEDS_HUMAN_REVIEW"),
            ("country_of_origin", "Nepal", "LOW", "NEEDS_HUMAN_REVIEW"),
        ],
        "violations": [
            {
                "field_name": "general",
                "reason": "Image is too dark (poorly lit). OCR confidence is low. Retake with better lighting.",
                "severity": "HIGH",
                "confidence": "LOW",
                "rule_id": None,
            }
        ],
    },
    {
        "product_name": "VitaCare Vitamin C Tablets",
        "status": "VERIFIED_COMPLIANT",
        "overall_confidence": "MEDIUM",
        "image_quality": "ACCEPTABLE",
        "template_name": "angled_label",
        "declarations": [
            ("product_name", "VitaCare Vitamin C Tablets", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("mrp", "₹199.00", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("net_quantity", "60 tabs", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("manufacturer", "VitaCare Pharma, Hyderabad", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("manufacturing_date", "June 2026", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("consumer_care", "040-1234-5678", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("country_of_origin", "India", "MEDIUM", "VERIFIED_COMPLIANT"),
            ("best_before", "May 2028", "MEDIUM", "VERIFIED_COMPLIANT"),
        ],
        "violations": [],
    },
]


def seed():
    print("\n=== SMART-LM Demo Data Seeder ===")
    print("WARNING: All data is SYNTHETIC - NOT real enforcement evidence\n")

    # Init DB
    init_db()

    print("\nSeeding demo users...")
    db = SessionLocal()
    demo_users = [
        {"username": "inspector", "password": "Inspector@123", "role": "INSPECTOR", "full_name": "Demo Inspector"},
        {"username": "reviewer", "password": "Reviewer@123", "role": "REVIEWER", "full_name": "Demo Reviewer"},
        {"username": "admin", "password": "Admin@123", "role": "ADMIN", "full_name": "Demo Admin"},
    ]
    try:
        for du in demo_users:
            if not db.query(User).filter(User.username == du["username"]).first():
                db.add(User(
                    username=du["username"],
                    hashed_password=get_password_hash(du["password"]),
                    role=du["role"],
                    full_name=du["full_name"],
                    email=f"{du['username']}@smartlm.demo"
                ))
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"ERROR seeding users: {exc}")
    finally:
        db.close()

    # Generate images
    print("Generating synthetic label images...")
    template_map = {t["name"]: t for t in LABEL_TEMPLATES}
    image_paths = {}
    for tmpl in LABEL_TEMPLATES:
        fname = f"demo_{tmpl['name']}.jpg"
        path = os.path.join(DEMO_DIR, fname)
        create_label_image(tmpl, path)
        # Also copy to data/test_images for reference
        import shutil
        shutil.copy(path, os.path.join(DATA_DIR, fname))
        image_paths[tmpl["name"]] = path

    print(f"\nSeeding {len(DEMO_INSPECTIONS)} demo inspections into database...")
    db = SessionLocal()

    base_time = datetime.utcnow() - timedelta(days=5)

    try:
        for i, demo in enumerate(DEMO_INSPECTIONS):
            iid = f"DEMO-{str(uuid.uuid4())[:8].upper()}"
            created = base_time + timedelta(hours=i * 6)
            tmpl_name = demo["template_name"]
            img_path = image_paths.get(tmpl_name, "")

            insp = Inspection(
                inspection_id=iid,
                created_at=created,
                product_name=demo["product_name"],
                status=demo["status"],
                overall_confidence=demo["overall_confidence"],
                image_path=img_path,
                image_quality=demo["image_quality"],
                ocr_text_length=random.randint(50, 300),
                is_demo=True,
            )
            db.add(insp)

            for field_name, value, conf, status in demo["declarations"]:
                db.add(Declaration(
                    inspection_id=iid,
                    field_name=field_name,
                    extracted_value=value,
                    confidence=conf,
                    status=status,
                ))

            for v in demo["violations"]:
                db.add(Violation(
                    inspection_id=iid,
                    field_name=v["field_name"],
                    reason=v["reason"],
                    severity=v["severity"],
                    confidence=v["confidence"],
                    rule_id=v.get("rule_id"),
                ))

            print(f"  [{i+1}] {iid} - {demo['product_name']} -> {demo['status']}")

        db.commit()
        print(f"\nSUCCESS: Demo data seeded successfully!")
        print("   Open the frontend and you should see 5 demo inspections in History.")

    except Exception as exc:
        db.rollback()
        print(f"\nERROR seeding data: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
