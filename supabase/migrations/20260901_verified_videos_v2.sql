-- Migration: 20260901_verified_videos_v2.sql
-- Description: Verified Arabic Instructional Videos, Medication-Device Mappings & Match Logs

-- 1. Table: verified_videos
CREATE TABLE IF NOT EXISTS public.verified_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    usage_topic TEXT NOT NULL,
    category TEXT,
    dosage_form TEXT,
    device_type TEXT,
    device_name TEXT,
    aliases TEXT[],
    language TEXT DEFAULT 'ar',
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    source_name TEXT NOT NULL,
    source_url TEXT,
    source_tier TEXT,
    verified BOOLEAN DEFAULT true,
    active BOOLEAN DEFAULT true,
    verification_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexing for verified_videos
CREATE INDEX IF NOT EXISTS idx_verified_videos_topic ON public.verified_videos(usage_topic);
CREATE INDEX IF NOT EXISTS idx_verified_videos_device ON public.verified_videos(device_name);
CREATE INDEX IF NOT EXISTS idx_verified_videos_status ON public.verified_videos(verified, active);
CREATE INDEX IF NOT EXISTS idx_verified_videos_aliases ON public.verified_videos USING GIN(aliases);

-- Enable RLS
ALTER TABLE public.verified_videos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public can view verified and active videos" ON public.verified_videos;
CREATE POLICY "Public can view verified and active videos" ON public.verified_videos
    FOR SELECT USING (verified = true AND active = true);

DROP POLICY IF EXISTS "Admins can manage verified videos" ON public.verified_videos;
CREATE POLICY "Admins can manage verified videos" ON public.verified_videos
    FOR ALL USING (auth.role() = 'service_role');


-- 2. Table: medication_device_mappings
CREATE TABLE IF NOT EXISTS public.medication_device_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generic_name TEXT NOT NULL,
    brand_name TEXT,
    aliases TEXT[],
    dosage_form TEXT,
    device_category TEXT,
    device_type TEXT,
    device_name TEXT,
    usage_topic TEXT,
    exact_device_verified BOOLEAN DEFAULT false,
    source_name TEXT,
    source_url TEXT,
    source_page TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexing for medication_device_mappings
CREATE INDEX IF NOT EXISTS idx_med_mappings_generic ON public.medication_device_mappings(generic_name);
CREATE INDEX IF NOT EXISTS idx_med_mappings_brand ON public.medication_device_mappings(brand_name);
CREATE INDEX IF NOT EXISTS idx_med_mappings_device ON public.medication_device_mappings(device_name);
CREATE INDEX IF NOT EXISTS idx_med_mappings_topic ON public.medication_device_mappings(usage_topic);
CREATE INDEX IF NOT EXISTS idx_med_mappings_active ON public.medication_device_mappings(active);
CREATE INDEX IF NOT EXISTS idx_med_mappings_aliases ON public.medication_device_mappings USING GIN(aliases);

-- Enable RLS
ALTER TABLE public.medication_device_mappings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public can view active medication device mappings" ON public.medication_device_mappings;
CREATE POLICY "Public can view active medication device mappings" ON public.medication_device_mappings
    FOR SELECT USING (active = true);

DROP POLICY IF EXISTS "Admins can manage medication device mappings" ON public.medication_device_mappings;
CREATE POLICY "Admins can manage medication device mappings" ON public.medication_device_mappings
    FOR ALL USING (auth.role() = 'service_role');


-- 3. Table: video_match_logs (Audit logging for video lookups)
CREATE TABLE IF NOT EXISTS public.video_match_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT,
    detected_medication TEXT,
    detected_brand TEXT,
    detected_usage_intent BOOLEAN,
    resolved_usage_topic TEXT,
    resolved_device TEXT,
    video_id UUID REFERENCES public.verified_videos(id) ON DELETE SET NULL,
    match_status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexing for video_match_logs
CREATE INDEX IF NOT EXISTS idx_video_match_logs_created ON public.video_match_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_match_logs_status ON public.video_match_logs(match_status);

-- Enable RLS
ALTER TABLE public.video_match_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Admins can manage video match logs" ON public.video_match_logs;
CREATE POLICY "Admins can manage video match logs" ON public.video_match_logs
    FOR ALL USING (auth.role() = 'service_role');
