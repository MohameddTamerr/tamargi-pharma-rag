-- Migration: 20260901_medication_forms.sql
-- Description: Structured Medication Forms, Routes, and Reviewable Device Candidates

-- 1. Create medication_forms table
CREATE TABLE IF NOT EXISTS public.medication_forms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generic_name TEXT NOT NULL,
    dosage_form_raw TEXT NOT NULL,
    dosage_form_normalized TEXT NOT NULL,
    strength TEXT,
    route_of_administration TEXT,
    administration_instructions TEXT,
    device_category TEXT,
    exact_device_name TEXT DEFAULT NULL,
    exact_device_verified BOOLEAN DEFAULT false,
    video_relevant TEXT DEFAULT 'false',
    source_file TEXT NOT NULL,
    source_page INTEGER NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Indexes for fast lookup & filtering
CREATE INDEX IF NOT EXISTS idx_med_forms_generic ON public.medication_forms(generic_name);
CREATE INDEX IF NOT EXISTS idx_med_forms_normalized ON public.medication_forms(dosage_form_normalized);
CREATE INDEX IF NOT EXISTS idx_med_forms_category ON public.medication_forms(device_category);
CREATE INDEX IF NOT EXISTS idx_med_forms_video_rel ON public.medication_forms(video_relevant);
CREATE INDEX IF NOT EXISTS idx_med_forms_source_file ON public.medication_forms(source_file);
CREATE INDEX IF NOT EXISTS idx_med_forms_active ON public.medication_forms(active);

-- 3. Enable Row Level Security
ALTER TABLE public.medication_forms ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies
DROP POLICY IF EXISTS "Public can view active medication forms" ON public.medication_forms;
CREATE POLICY "Public can view active medication forms" ON public.medication_forms
    FOR SELECT USING (active = true);

DROP POLICY IF EXISTS "Admins can manage medication forms" ON public.medication_forms;
CREATE POLICY "Admins can manage medication forms" ON public.medication_forms
    FOR ALL USING (auth.role() = 'service_role');
