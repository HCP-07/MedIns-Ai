from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_bills(output_dir="sample_bills"):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Legitimate Claim Bill
    img1 = Image.new('RGB', (700, 450), color=(250, 250, 250))
    d1 = ImageDraw.Draw(img1)
    
    # Draw header
    d1.rectangle([(0, 0), (700, 60)], fill=(30, 80, 160))
    d1.text((20, 18), "CITY GENERAL HOSPITAL - OFFICIAL INVOICE", fill=(255, 255, 255))
    
    body_text_1 = """
PATIENT: John Doe                     CLAIM DATE: 2026-08-01
PATIENT ID: PAT-49201                 HOSPITAL ID: HOSP-112

DIAGNOSIS: Acute Appendicitis (ICD-10 K35.80)
PROCEDURE BILLED: Laparoscopic Cholecystectomy / Appendectomy (CPT-47562)

ITEMIZED BREAKDOWN:
- Operating Room Fee: $3,500.00
- Anesthesia & Supplies: $1,800.00
- Surgeon Professional Fee: $1,200.00

TOTAL CLAIM AMOUNT: $6,500.00
STATUS: Pending Insurance Review
"""
    d1.text((30, 80), body_text_1, fill=(20, 20, 20))
    img1.save(os.path.join(output_dir, "legitimate_claim.png"))

    # 2. Fraudulent Upcoded Claim Bill
    img2 = Image.new('RGB', (700, 480), color=(255, 245, 245))
    d2 = ImageDraw.Draw(img2)
    
    d2.rectangle([(0, 0), (700, 60)], fill=(180, 40, 40))
    d2.text((20, 18), "METRO CARE CLINIC - MEDICAL INVOICE", fill=(255, 255, 255))
    
    body_text_2 = """
PATIENT: Jane Smith                   CLAIM DATE: 2026-08-04
PATIENT ID: PAT-88210                 HOSPITAL ID: HOSP-145

DIAGNOSIS: Mild Acute Ankle Sprain (ICD-10 S93.401A)
PROCEDURE BILLED: Lumbar Spine MRI & Trauma Coding (CPT-72148)

ITEMIZED BREAKDOWN:
- Routine Ankle Examination: $150.00
- Lumbar Spine Contrast MRI: $4,500.00 [UPCODED]
- Emergency High-Trauma Facility Fee: $3,850.00

TOTAL CLAIM AMOUNT: $8,500.00 (Benchmark: $1,400.00)
STATUS: Pending Fraud Investigation
"""
    d2.text((30, 80), body_text_2, fill=(20, 20, 20))
    img2.save(os.path.join(output_dir, "fraudulent_upcoded_claim.png"))
    print(f"Sample bill images created in '{output_dir}/'")

if __name__ == "__main__":
    create_sample_bills()
