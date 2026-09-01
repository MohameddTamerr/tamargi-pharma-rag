# Tamargi.ai — Explainable Medication Evidence Assistant & Patient Education Platform

Tamargi.ai is a grounded, explainable pharmaceutical AI assistant built for the Egyptian healthcare context. It pairs strict Hybrid RAG evidence retrieval from Egyptian Drug Authority (EDA) formularies with a high-precision **Verified Instructional Video Delivery System**.

---

## 1. Verified Medical Instructional Video Feature

The Verified Video feature delivers approved, patient-friendly visual instructions for physical medication devices and delivery systems (e.g. Inhalers, Nebulizers, Insulin Pens, Eye/Ear Drops, Nasal Sprays, Suppositories, and Patches).

### Architecture & Matching Hierarchy
Videos are supplementary patient-education assets and are **never** injected into the RAG context or treated as clinical evidence. The matching logic strictly enforces a 4-tier hierarchy:

```
User Query
   ↓
Detect Practical Usage Intent (e.g. "ازاي استخدم البخاخ؟" / "How do I use this inhaler?")
   [Clinical questions like contraindications, adverse effects, or dosages are strictly suppressed]
   ↓
Check Physical Form & Safety Exclusions:
   ├─ Topical aerosols (e.g., Lidocaine spray, Terbinafine aerosol) -> NOT respiratory inhalers -> NO video
   ├─ Nebulizer solutions -> Generic nebulizer technique (nebulizer_usage)
   ├─ Rectal suppositories -> rectal_suppository_usage (Separated from vaginal pessaries)
   └─ Vaginal pessaries -> vaginal_pessary_usage (Separated from rectal suppositories)
   ↓
Matching Priority:
   Tier 1: Exact Brand + Exact Device (e.g. Symbicort Turbohaler -> turbohaler_usage)
   Tier 2: Exact Verified Device (e.g. Ellipta, Respimat, HandiHaler, Accuhaler, Breezhaler)
   Tier 3: Approved Generic Technique (e.g. generic pMDI, eye drops, ear drops, nasal spray, patches)
   Tier 4: No Video / Exact Device Unknown:
           If a DPI/multi-device medication has an unknown commercial device, NO device is guessed.
           The system returns `found: false, reason: "exact_device_unknown"` and prompts for the brand name.
```

### Approved Usage Topics Taxonomy
- **Inhalation Devices**: `turbohaler_usage`, `ellipta_usage`, `diskus_usage`, `respimat_usage`, `handihaler_usage`, `breezhaler_usage`, `genuair_usage`, `forspiro_usage`, `nexthaler_usage`, `novolizer_usage`, `spiromax_usage`, `autohaler_usage`, `pmdi_usage`, `aerochamber_usage`, `vortex_spacer_usage`
- **Nebulizers**: `nebulizer_usage`
- **Diabetes & Self-Injections**: `insulin_pen_usage`, `subcutaneous_self_injection_usage`
- **Ophthalmic**: `eye_drop_usage`, `eye_ointment_usage`
- **Otic**: `ear_drop_usage`
- **Nasal**: `nasal_spray_usage`, `nasal_drop_usage`
- **Rectal & Vaginal**: `rectal_suppository_usage`, `vaginal_pessary_usage`
- **Transdermal**: `transdermal_patch_usage`

---

## 2. API Endpoints

### `POST /api/video/lookup`
Performs verified instructional video lookups.

**Request Body:**
```json
{
  "query_text": "ازاي استخدم بخاخ التربوهيلر؟",
  "generic_name": null,
  "brand_name": null,
  "dosage_form": null,
  "device_name": null
}
```

**Response (`found = true`):**
```json
{
  "found": true,
  "title": "طريقة استخدام بخاخ التربوهيلر (Turbohaler)",
  "video_url": "https://example.com/verified/turbohaler_ar.mp4",
  "thumbnail_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae",
  "source_name": "Egyptian Respiratory Society",
  "source_url": "https://ers.org.eg",
  "usage_topic": "turbohaler_usage",
  "device_name": "Turbohaler",
  "language": "ar"
}
```

**Response (`found = false`):**
```json
{
  "found": false,
  "reason": "exact_device_unknown",
  "helper_prompt": "الدواء ده ممكن يكون متوفر بأكثر من جهاز. ابعتلي اسم الـbrand أو اسم الجهاز المكتوب على العبوة عشان أجيبلك فيديو الاستخدام الصحيح."
}
```

### `POST /api/chat`
Conversational RAG assistant returning grounded answers, citations, and attached verified instructional videos.

---

## 3. Database Schema (Supabase)

- **`public.verified_videos`**: Stores approved instructional video metadata (`title`, `usage_topic`, `category`, `dosage_form`, `device_type`, `device_name`, `language`, `video_url`, `thumbnail_url`, `source_name`, `verified`, `active`).
- **`public.medication_device_mappings`**: Connects pharmaceutical active ingredients, commercial brand names, and dosage forms to delivery systems.
- **`public.video_match_logs`**: Audits runtime matching decisions, user queries, resolved topics, and match statuses.

Migrations are located in [`supabase/migrations/20260901_verified_videos_v2.sql`](file:///c:/Users/user/Downloads/tamargi-pharma-rag/supabase/migrations/20260901_verified_videos_v2.sql).

---

## 4. Verification & Testing

To run the automated video matching test suite covering all 10 scenarios:
```bash
python backend/test_verified_video_feature.py
```
