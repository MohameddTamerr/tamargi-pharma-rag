-- Migration: 20260901_exact_device_matching.sql
-- Description: Exact Device/Delivery-System Matching and Medication-Device Mappings

-- 1. Safely extend verified_videos table with taxonomy columns
ALTER TABLE public.verified_videos 
    ADD COLUMN IF NOT EXISTS category TEXT,
    ADD COLUMN IF NOT EXISTS dosage_form TEXT,
    ADD COLUMN IF NOT EXISTS device_type TEXT,
    ADD COLUMN IF NOT EXISTS device_name TEXT,
    ADD COLUMN IF NOT EXISTS usage_topic TEXT;

-- 2. Create Medication-to-Device Mappings Table
CREATE TABLE IF NOT EXISTS public.medication_device_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medication_name TEXT,
    brand_name TEXT NOT NULL,
    aliases TEXT[],
    dosage_form TEXT,
    device_category TEXT NOT NULL,
    device_type TEXT,
    device_name TEXT NOT NULL,
    usage_topic TEXT NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_verified_videos_device_name ON public.verified_videos(device_name);
CREATE INDEX IF NOT EXISTS idx_verified_videos_usage_topic ON public.verified_videos(usage_topic);
CREATE INDEX IF NOT EXISTS idx_med_mappings_brand ON public.medication_device_mappings(brand_name);
CREATE INDEX IF NOT EXISTS idx_med_mappings_device ON public.medication_device_mappings(device_name);
CREATE INDEX IF NOT EXISTS idx_med_mappings_usage_topic ON public.medication_device_mappings(usage_topic);
CREATE INDEX IF NOT EXISTS idx_med_mappings_active ON public.medication_device_mappings(active);
CREATE INDEX IF NOT EXISTS idx_med_mappings_aliases ON public.medication_device_mappings USING GIN(aliases);

-- 4. Enable Row Level Security
ALTER TABLE public.medication_device_mappings ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies
DROP POLICY IF EXISTS "Public can view active medication device mappings" ON public.medication_device_mappings;
CREATE POLICY "Public can view active medication device mappings" ON public.medication_device_mappings
    FOR SELECT USING (active = true);

DROP POLICY IF EXISTS "Admins can manage medication device mappings" ON public.medication_device_mappings;
CREATE POLICY "Admins can manage medication device mappings" ON public.medication_device_mappings
    FOR ALL USING (auth.role() = 'service_role');
