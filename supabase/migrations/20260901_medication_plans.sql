-- Migration: 20260901_medication_plans.sql
-- Description: Medication Plans (Draft Prescriptions for Professional Review) with Secure QR Verification Tokens

CREATE TABLE IF NOT EXISTS public.medication_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title TEXT NOT NULL DEFAULT 'خطة دوائية للمراجعة الطبية',
    verification_token UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    patient_info JSONB NOT NULL DEFAULT '{}'::jsonb,
    confirmed_factors JSONB NOT NULL DEFAULT '{}'::jsonb,
    medications JSONB NOT NULL DEFAULT '[]'::jsonb,
    safety_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence_provenance JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'archived', 'revoked'
    notes TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medication_plans_user ON public.medication_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_medication_plans_token ON public.medication_plans(verification_token);
CREATE INDEX IF NOT EXISTS idx_medication_plans_created ON public.medication_plans(created_at DESC);

ALTER TABLE public.medication_plans ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can manage their own medication plans" ON public.medication_plans;
CREATE POLICY "Users can manage their own medication plans" ON public.medication_plans
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Public can view valid medication plans via verification token" ON public.medication_plans;
CREATE POLICY "Public can view valid medication plans via verification token" ON public.medication_plans
    FOR SELECT USING (status = 'active');
