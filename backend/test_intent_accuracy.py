import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.orchestrator.intents import detect_intents, IntentType

routing_prompts = [
    # 1-4: General Med
    ("ما هي دواعي استعمال الباراسيتامول؟", IntentType.GENERAL_MEDICATION_QUESTION),
    ("What is Metformin used for?", IntentType.GENERAL_MEDICATION_QUESTION),
    ("جرعة دواء كونكور 5 ملجم", IntentType.GENERAL_MEDICATION_QUESTION),
    ("ما هي فوائد كبسولات اوميبرازول؟", IntentType.GENERAL_MEDICATION_QUESTION),

    # 5-8: Personalized Safety
    ("ينفع آخد ديكساميثازون؟", IntentType.MEDICATION_SAFETY),
    ("Can I take Ibuprofen with kidney disease?", IntentType.MEDICATION_SAFETY),
    ("هل دواء اسبوسيد آمن مع قرحة المعدة؟", IntentType.MEDICATION_SAFETY),
    ("ينفع اخد حبوب ميتفورمين وانا حامل؟", IntentType.MEDICATION_SAFETY),

    # 9-12: Comparison
    ("ما الفرق بين الباراسيتامول والإيبوبروفين؟", IntentType.DRUG_COMPARISON),
    ("ايه الفرق بين Panadol و Brufen؟", IntentType.DRUG_COMPARISON),
    ("What is the difference between Amoxicillin and Augmentin?", IntentType.DRUG_COMPARISON),
    ("مقارنة بين اوميبرازول و بانتوبرازول", IntentType.DRUG_COMPARISON),

    # 13-16: Interaction
    ("هل يتعارض السيلدينافيل مع النيتروجليسرين؟", IntentType.DRUG_INTERACTION),
    ("ينفع اخد بروفين مع وارفارين؟", IntentType.DRUG_INTERACTION),
    ("Is there an interaction between Clopidogrel and Omeprazole?", IntentType.DRUG_INTERACTION),
    ("ينفع اخد سبيكترا مع كابوتين؟", IntentType.DRUG_INTERACTION),

    # 17-20: Symptom
    ("عندي صداع وسخونية بقالهم يومين", IntentType.SYMPTOM_QUESTION),
    ("حاسس بمغص وتقلصات شديدة في البطن", IntentType.SYMPTOM_QUESTION),
    ("I have a dry cough and runny nose", IntentType.SYMPTOM_QUESTION),
    ("عندي دوخة وزغللة في العين", IntentType.SYMPTOM_QUESTION),

    # 21-24: Device Usage
    ("ازاي استخدم جهاز Turbohaler؟", IntentType.DEVICE_USAGE),
    ("طريقة استخدام بخاخ Ellipta", IntentType.DEVICE_USAGE),
    ("ازاي استخدم البخاخ؟", IntentType.DEVICE_USAGE),
    ("كيفية استخدام قلم الانسولين", IntentType.DEVICE_USAGE),

    # 25-28: Medication Plan
    ("اعمل لي خطة دوائية لمراجعة دواء باراسيتامول", IntentType.MEDICATION_PLAN_REQUEST),
    ("Create a medication plan for my prescriptions", IntentType.MEDICATION_PLAN_REQUEST),
    ("عايز روشتة ومراجعة دوائية للادوية بتاعتي", IntentType.MEDICATION_PLAN_REQUEST),
    ("سجل لي جدول وخطة للأدوية", IntentType.MEDICATION_PLAN_REQUEST),

    # 29-32: Confirmation & Profile
    ("ايوه عندي", IntentType.CONFIRMATION_RESPONSE),
    ("لا مش عندي", IntentType.CONFIRMATION_RESPONSE),
    ("انا عندي حساسية من البنسلين ضيفها للملف", IntentType.PATIENT_PROFILE_UPDATE),
    ("نصائح عامة لصحة القلب وتناول المياه", IntentType.GENERAL_HEALTH_QUESTION)
]

correct = 0
for q, exp in routing_prompts:
    has_pending = (exp == IntentType.CONFIRMATION_RESPONSE)
    res = detect_intents(q, has_pending_confirmation=has_pending)
    act = res.primary_intent if res else None
    if act == exp:
        correct += 1
    else:
        print(f"MISMATCH: Q: \"{q}\"\n  -> Exp: {exp.value} | Act: {act.value if act else None}")

print(f"\nAccuracy: {correct} / {len(routing_prompts)} ({correct / len(routing_prompts) * 100:.1f}%)")
