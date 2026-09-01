-- Migration: 20260901_patient_safety_engine.sql
-- Description: Structured Patient Profile, Conditions, Allergies, Medications, Medical History, and Pending Confirmations

-- 1. Table: patient_profiles
CREATE TABLE IF NOT EXISTS public.patient_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,
    date_of_birth DATE,
    sex TEXT,
    pregnancy_status TEXT, -- 'none', 'pregnant_first_trimester', 'pregnant_second_trimester', 'pregnant_third_trimester', 'planning_pregnancy'
    breastfeeding_status TEXT, -- 'none', 'breastfeeding'
    weight_kg NUMERIC(5, 2),
    height_cm NUMERIC(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_profiles_user ON public.patient_profiles(user_id);
ALTER TABLE public.patient_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own profile" ON public.patient_profiles;
CREATE POLICY "Users can manage their own profile" ON public.patient_profiles
    FOR ALL USING (auth.uid() = user_id);


-- 2. Table: patient_conditions
CREATE TABLE IF NOT EXISTS public.patient_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    condition_name TEXT NOT NULL,
    normalized_condition TEXT NOT NULL,
    status TEXT DEFAULT 'active', -- 'active', 'managed', 'resolved'
    confirmed BOOLEAN DEFAULT false,
    last_confirmed_at TIMESTAMP WITH TIME ZONE,
    source TEXT DEFAULT 'chat', -- 'chat', 'profile', 'physician'
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_conditions_user ON public.patient_conditions(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_conditions_norm ON public.patient_conditions(normalized_condition);
CREATE INDEX IF NOT EXISTS idx_patient_conditions_active ON public.patient_conditions(active);
ALTER TABLE public.patient_conditions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own conditions" ON public.patient_conditions;
CREATE POLICY "Users can manage their own conditions" ON public.patient_conditions
    FOR ALL USING (auth.uid() = user_id);


-- 3. Table: patient_allergies
CREATE TABLE IF NOT EXISTS public.patient_allergies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    allergen TEXT NOT NULL,
    normalized_allergen TEXT NOT NULL,
    reaction TEXT,
    severity TEXT, -- 'mild', 'moderate', 'severe_anaphylaxis'
    confirmed BOOLEAN DEFAULT false,
    last_confirmed_at TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_allergies_user ON public.patient_allergies(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_allergies_norm ON public.patient_allergies(normalized_allergen);
CREATE INDEX IF NOT EXISTS idx_patient_allergies_active ON public.patient_allergies(active);
ALTER TABLE public.patient_allergies ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own allergies" ON public.patient_allergies;
CREATE POLICY "Users can manage their own allergies" ON public.patient_allergies
    FOR ALL USING (auth.uid() = user_id);


-- 4. Table: patient_medications
CREATE TABLE IF NOT EXISTS public.patient_medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    generic_name TEXT NOT NULL,
    brand_name TEXT,
    strength TEXT,
    dosage_form TEXT,
    dose TEXT,
    frequency TEXT,
    indication TEXT,
    confirmed BOOLEAN DEFAULT false,
    last_confirmed_at TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_medications_user ON public.patient_medications(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_medications_gen ON public.patient_medications(generic_name);
CREATE INDEX IF NOT EXISTS idx_patient_medications_active ON public.patient_medications(active);
ALTER TABLE public.patient_medications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own medications" ON public.patient_medications;
CREATE POLICY "Users can manage their own medications" ON public.patient_medications
    FOR ALL USING (auth.uid() = user_id);


-- 5. Table: patient_medical_history
CREATE TABLE IF NOT EXISTS public.patient_medical_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    history_type TEXT NOT NULL, -- 'surgery', 'hospitalization', 'previous_adverse_reaction', 'pregnancy_history', 'other'
    value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    confirmed BOOLEAN DEFAULT false,
    last_confirmed_at TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_history_user ON public.patient_medical_history(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_history_type ON public.patient_medical_history(history_type);
CREATE INDEX IF NOT EXISTS idx_patient_history_active ON public.patient_medical_history(active);
ALTER TABLE public.patient_medical_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own medical history" ON public.patient_medical_history;
CREATE POLICY "Users can manage their own medical history" ON public.patient_medical_history
    FOR ALL USING (auth.uid() = user_id);


-- 6. Table: pending_medical_confirmations
CREATE TABLE IF NOT EXISTS public.pending_medical_confirmations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    conversation_id TEXT NOT NULL,
    fact_type TEXT NOT NULL, -- 'condition', 'allergy', 'medication', 'history', 'pregnancy'
    fact_id UUID,
    normalized_value TEXT NOT NULL,
    original_question TEXT NOT NULL,
    medication_context TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'confirmed', 'denied', 'expired'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_pending_confirmations_user ON public.pending_medical_confirmations(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_conv ON public.pending_medical_confirmations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_status ON public.pending_medical_confirmations(status);
ALTER TABLE public.pending_medical_confirmations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own pending confirmations" ON public.pending_medical_confirmations;
CREATE POLICY "Users can manage their own pending confirmations" ON public.pending_medical_confirmations
    FOR ALL USING (auth.uid() = user_id);
