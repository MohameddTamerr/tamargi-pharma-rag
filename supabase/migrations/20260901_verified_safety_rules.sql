-- Migration: 20260901_verified_safety_rules.sql
-- Description: Verified Medication Safety Knowledge Store (Structured Clinical Rules with Strict Evidence Traceability)

CREATE TABLE IF NOT EXISTS public.verified_safety_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type TEXT NOT NULL, -- 'allergy', 'drug_disease', 'drug_drug', 'high_alert', 'do_not_crush', 'pregnancy', 'breastfeeding'
    drug_a TEXT NOT NULL,
    drug_b TEXT,
    condition_name TEXT,
    allergen_class TEXT,
    dosage_form TEXT,
    status TEXT NOT NULL, -- 'contraindicated', 'warning', 'caution', 'safe_no_known_issue'
    reason TEXT,
    source_file TEXT NOT NULL,
    source_page INTEGER NOT NULL,
    source_monograph TEXT,
    source_section TEXT,
    evidence_excerpt TEXT NOT NULL,
    source_authority TEXT DEFAULT 'Egyptian Drug Authority',
    verified BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verified_rules_type ON public.verified_safety_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_verified_rules_drug_a ON public.verified_safety_rules(drug_a);
CREATE INDEX IF NOT EXISTS idx_verified_rules_drug_b ON public.verified_safety_rules(drug_b);
CREATE INDEX IF NOT EXISTS idx_verified_rules_cond ON public.verified_safety_rules(condition_name);
CREATE INDEX IF NOT EXISTS idx_verified_rules_active_ver ON public.verified_safety_rules(active, verified);

ALTER TABLE public.verified_safety_rules ENABLE ROW LEVEL SECURITY;

-- RLS Policies: verified_safety_rules
DROP POLICY IF EXISTS "Public can view verified safety rules" ON public.verified_safety_rules;
CREATE POLICY "Public can view verified safety rules" ON public.verified_safety_rules
    FOR SELECT USING (active = true AND verified = true);

DROP POLICY IF EXISTS "Admins can manage verified safety rules" ON public.verified_safety_rules;
CREATE POLICY "Admins can manage verified safety rules" ON public.verified_safety_rules
    FOR ALL USING (auth.role() = 'service_role');
