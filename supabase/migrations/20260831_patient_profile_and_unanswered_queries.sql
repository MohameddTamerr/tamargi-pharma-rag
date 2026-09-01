-- Migration: Patient Profile Extension & Unanswered Queries Logging
-- Date: 2026-08-31

-- 1. Extend Patient Profile
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS birth_date DATE;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS gender TEXT CHECK (gender IN ('male', 'female'));
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS weight_kg NUMERIC(5,2);

-- 2. Patient Conditions Table
CREATE TABLE IF NOT EXISTS public.patient_conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    condition_name TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    confirmed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Patient Allergies Table
CREATE TABLE IF NOT EXISTS public.patient_allergies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    allergy_name TEXT NOT NULL,
    confirmed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Patient Current Medications Table
CREATE TABLE IF NOT EXISTS public.patient_medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    medication_name TEXT NOT NULL,
    dose_text TEXT,
    frequency_text TEXT,
    status TEXT DEFAULT 'active',
    confirmed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Unanswered Queries Table (Insufficient Evidence Logging)
CREATE TABLE IF NOT EXISTS public.unanswered_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE SET NULL,
    message_id UUID REFERENCES public.messages(id) ON DELETE SET NULL,
    original_query TEXT NOT NULL,
    normalized_query TEXT,
    language_detected TEXT,
    reason TEXT DEFAULT 'insufficient_evidence',
    top_retrieved_sources JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT false,
    resolution_note TEXT
);

-- Indexing for Query Optimization & Analytics Filters
CREATE INDEX IF NOT EXISTS idx_patient_conditions_user ON public.patient_conditions(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_allergies_user ON public.patient_allergies(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_medications_user ON public.patient_medications(user_id);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_created ON public.unanswered_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_user ON public.unanswered_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_lang ON public.unanswered_queries(language_detected);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_resolved ON public.unanswered_queries(resolved);

-- 6. Enable Row Level Security
ALTER TABLE public.patient_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_allergies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.unanswered_queries ENABLE ROW LEVEL SECURITY;

-- RLS Policies: patient_conditions
CREATE POLICY "Users can view their own conditions" ON public.patient_conditions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own conditions" ON public.patient_conditions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own conditions" ON public.patient_conditions
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own conditions" ON public.patient_conditions
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies: patient_allergies
CREATE POLICY "Users can view their own allergies" ON public.patient_allergies
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own allergies" ON public.patient_allergies
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own allergies" ON public.patient_allergies
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own allergies" ON public.patient_allergies
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies: patient_medications
CREATE POLICY "Users can view their own medications" ON public.patient_medications
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own medications" ON public.patient_medications
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own medications" ON public.patient_medications
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own medications" ON public.patient_medications
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies: unanswered_queries
CREATE POLICY "Users can view their own unanswered queries" ON public.unanswered_queries
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "Users or backend can insert unanswered queries" ON public.unanswered_queries
    FOR INSERT WITH CHECK (user_id IS NULL OR auth.uid() = user_id);

-- 7. Strengthen Messages Insert Policy
DROP POLICY IF EXISTS "Users can insert messages in their conversations" ON public.messages;
CREATE POLICY "Users can insert messages in their conversations" ON public.messages
    FOR INSERT WITH CHECK (
        auth.uid() = messages.user_id AND
        EXISTS (
            SELECT 1 FROM public.conversations c
            WHERE c.id = messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );
