-- Migration: 20260901_verified_videos.sql
-- Description: Verified Medical Instructional Videos table with Row Level Security

-- 1. Create Verified Videos Table
CREATE TABLE IF NOT EXISTS public.verified_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    medication_or_device TEXT NOT NULL,
    aliases TEXT[],
    language TEXT DEFAULT 'en',
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    source_name TEXT NOT NULL,
    source_url TEXT,
    verified BOOLEAN DEFAULT true,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Indexes for fast concept and alias lookup
CREATE INDEX IF NOT EXISTS idx_verified_videos_topic ON public.verified_videos(topic);
CREATE INDEX IF NOT EXISTS idx_verified_videos_medication ON public.verified_videos(medication_or_device);
CREATE INDEX IF NOT EXISTS idx_verified_videos_status ON public.verified_videos(verified, active);
CREATE INDEX IF NOT EXISTS idx_verified_videos_aliases ON public.verified_videos USING GIN(aliases);

-- 3. Enable Row Level Security
ALTER TABLE public.verified_videos ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policy: Public read-only access for verified and active videos only
DROP POLICY IF EXISTS "Public can view verified and active videos" ON public.verified_videos;
CREATE POLICY "Public can view verified and active videos" ON public.verified_videos
    FOR SELECT USING (verified = true AND active = true);

-- 5. RLS Policy: Service role or admin write access
DROP POLICY IF EXISTS "Admins can manage verified videos" ON public.verified_videos;
CREATE POLICY "Admins can manage verified videos" ON public.verified_videos
    FOR ALL USING (auth.role() = 'service_role');
