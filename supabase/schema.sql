-- Tamargi.ai Supabase Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Profiles Table (Extended with personalization fields)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    preferred_language TEXT DEFAULT 'ar',
    birth_date DATE,
    gender TEXT CHECK (gender IN ('male', 'female')),
    weight_kg NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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

-- 5. Conversations Table
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'جديد محادثة',
    language TEXT DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Messages Table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    input_type TEXT DEFAULT 'text' CHECK (input_type IN ('text', 'voice')),
    normalized_query TEXT,
    language_detected TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Message Sources (Verified Evidence Citations)
CREATE TABLE IF NOT EXISTS public.message_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
    evidence_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    chunk_id INTEGER,
    rank INTEGER NOT NULL,
    score DOUBLE PRECISION,
    excerpt TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Feedback Table
CREATE TABLE IF NOT EXISTS public.feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating IN (1, -1)),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Unanswered Queries Table (Insufficient Evidence Logging)
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

-- Indexing for performance and analytics
CREATE INDEX IF NOT EXISTS idx_conversations_user ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_sources_message ON public.message_sources(message_id);
CREATE INDEX IF NOT EXISTS idx_feedback_message ON public.feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_patient_conditions_user ON public.patient_conditions(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_allergies_user ON public.patient_allergies(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_medications_user ON public.patient_medications(user_id);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_created ON public.unanswered_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_user ON public.unanswered_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_lang ON public.unanswered_queries(language_detected);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_resolved ON public.unanswered_queries(resolved);

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_allergies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.unanswered_queries ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Profiles
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies: Conversations
CREATE POLICY "Users can view their own conversations" ON public.conversations
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own conversations" ON public.conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own conversations" ON public.conversations
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own conversations" ON public.conversations
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies: Messages (Strengthened to verify user_id AND conversation ownership)
CREATE POLICY "Users can view messages in their conversations" ON public.messages
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert messages in their conversations" ON public.messages
    FOR INSERT WITH CHECK (
        auth.uid() = messages.user_id AND
        EXISTS (
            SELECT 1 FROM public.conversations c
            WHERE c.id = messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );

-- RLS Policies: Message Sources
CREATE POLICY "Users can view sources of their messages" ON public.message_sources
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.messages m
            WHERE m.id = message_sources.message_id
            AND m.user_id = auth.uid()
        )
    );

-- RLS Policies: Feedback
CREATE POLICY "Users can view their own feedback" ON public.feedback
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can submit feedback" ON public.feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

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

-- Trigger for Automatic Profile Creation on Supabase Auth Signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 10. Verified Medical Instructional Videos Table
CREATE TABLE IF NOT EXISTS public.verified_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    medication_or_device TEXT NOT NULL,
    aliases TEXT[],
    category TEXT,
    dosage_form TEXT,
    device_type TEXT,
    device_name TEXT,
    usage_topic TEXT,
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

-- Indexing for verified_videos
CREATE INDEX IF NOT EXISTS idx_verified_videos_topic ON public.verified_videos(topic);
CREATE INDEX IF NOT EXISTS idx_verified_videos_medication ON public.verified_videos(medication_or_device);
CREATE INDEX IF NOT EXISTS idx_verified_videos_device_name ON public.verified_videos(device_name);
CREATE INDEX IF NOT EXISTS idx_verified_videos_usage_topic ON public.verified_videos(usage_topic);
CREATE INDEX IF NOT EXISTS idx_verified_videos_status ON public.verified_videos(verified, active);
CREATE INDEX IF NOT EXISTS idx_verified_videos_aliases ON public.verified_videos USING GIN(aliases);

-- Enable RLS on verified_videos
ALTER TABLE public.verified_videos ENABLE ROW LEVEL SECURITY;

-- RLS Policies: verified_videos (Public can view verified and active only)
CREATE POLICY "Public can view verified and active videos" ON public.verified_videos
    FOR SELECT USING (verified = true AND active = true);
CREATE POLICY "Admins can manage verified videos" ON public.verified_videos
    FOR ALL USING (auth.role() = 'service_role');

-- 11. Medication-to-Device Mappings Table
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

-- Indexing for medication_device_mappings
CREATE INDEX IF NOT EXISTS idx_med_mappings_brand ON public.medication_device_mappings(brand_name);
CREATE INDEX IF NOT EXISTS idx_med_mappings_device ON public.medication_device_mappings(device_name);
CREATE INDEX IF NOT EXISTS idx_med_mappings_usage_topic ON public.medication_device_mappings(usage_topic);
CREATE INDEX IF NOT EXISTS idx_med_mappings_active ON public.medication_device_mappings(active);
CREATE INDEX IF NOT EXISTS idx_med_mappings_aliases ON public.medication_device_mappings USING GIN(aliases);

-- Enable RLS on medication_device_mappings
ALTER TABLE public.medication_device_mappings ENABLE ROW LEVEL SECURITY;

-- RLS Policies: medication_device_mappings
CREATE POLICY "Public can view active medication device mappings" ON public.medication_device_mappings
    FOR SELECT USING (active = true);
CREATE POLICY "Admins can manage medication device mappings" ON public.medication_device_mappings
    FOR ALL USING (auth.role() = 'service_role');

-- 12. Structured Medication Forms Table (EDA PDF Extraction)
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

-- Indexing for medication_forms
CREATE INDEX IF NOT EXISTS idx_med_forms_generic ON public.medication_forms(generic_name);
CREATE INDEX IF NOT EXISTS idx_med_forms_normalized ON public.medication_forms(dosage_form_normalized);
CREATE INDEX IF NOT EXISTS idx_med_forms_category ON public.medication_forms(device_category);
CREATE INDEX IF NOT EXISTS idx_med_forms_video_rel ON public.medication_forms(video_relevant);
CREATE INDEX IF NOT EXISTS idx_med_forms_source_file ON public.medication_forms(source_file);
CREATE INDEX IF NOT EXISTS idx_med_forms_active ON public.medication_forms(active);

-- Enable RLS on medication_forms
ALTER TABLE public.medication_forms ENABLE ROW LEVEL SECURITY;

-- RLS Policies: medication_forms
CREATE POLICY "Public can view active medication forms" ON public.medication_forms
    FOR SELECT USING (active = true);
CREATE POLICY "Admins can manage medication forms" ON public.medication_forms
    FOR ALL USING (auth.role() = 'service_role');

-- 13. Video Match Logs Table (Audit Trail)
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

-- Enable RLS on video_match_logs
ALTER TABLE public.video_match_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies: video_match_logs
CREATE POLICY "Admins can manage video match logs" ON public.video_match_logs
    FOR ALL USING (auth.role() = 'service_role');

-- 14. Patient Profiles Table
CREATE TABLE IF NOT EXISTS public.patient_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,
    date_of_birth DATE,
    sex TEXT,
    pregnancy_status TEXT,
    breastfeeding_status TEXT,
    weight_kg NUMERIC(5, 2),
    height_cm NUMERIC(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patient_profiles_user ON public.patient_profiles(user_id);
ALTER TABLE public.patient_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own profile" ON public.patient_profiles
    FOR ALL USING (auth.uid() = user_id);

-- 15. Patient Conditions Table
CREATE TABLE IF NOT EXISTS public.patient_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    condition_name TEXT NOT NULL,
    normalized_condition TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    confirmed BOOLEAN DEFAULT false,
    last_confirmed_at TIMESTAMP WITH TIME ZONE,
    source TEXT DEFAULT 'chat',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patient_conditions_user ON public.patient_conditions(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_conditions_norm ON public.patient_conditions(normalized_condition);
ALTER TABLE public.patient_conditions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own conditions" ON public.patient_conditions
    FOR ALL USING (auth.uid() = user_id);

-- 16. Patient Allergies Table
CREATE TABLE IF NOT EXISTS public.patient_allergies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    allergen TEXT NOT NULL,
    normalized_allergen TEXT NOT NULL,
    reaction TEXT,
    severity TEXT,
    confirmed BOOLEAN DEFAULT false,
    last_confirmed_at TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patient_allergies_user ON public.patient_allergies(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_allergies_norm ON public.patient_allergies(normalized_allergen);
ALTER TABLE public.patient_allergies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own allergies" ON public.patient_allergies
    FOR ALL USING (auth.uid() = user_id);

-- 17. Patient Medications Table
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
ALTER TABLE public.patient_medications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own medications" ON public.patient_medications
    FOR ALL USING (auth.uid() = user_id);

-- 18. Patient Medical History Table
CREATE TABLE IF NOT EXISTS public.patient_medical_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    history_type TEXT NOT NULL,
    value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    confirmed BOOLEAN DEFAULT false,
    last_confirmed_at TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patient_history_user ON public.patient_medical_history(user_id);
ALTER TABLE public.patient_medical_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own medical history" ON public.patient_medical_history
    FOR ALL USING (auth.uid() = user_id);

-- 19. Pending Medical Confirmations Table
CREATE TABLE IF NOT EXISTS public.pending_medical_confirmations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    conversation_id TEXT NOT NULL,
    fact_type TEXT NOT NULL,
    fact_id UUID,
    normalized_value TEXT NOT NULL,
    original_question TEXT NOT NULL,
    medication_context TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_user ON public.pending_medical_confirmations(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_conv ON public.pending_medical_confirmations(conversation_id);
ALTER TABLE public.pending_medical_confirmations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own pending confirmations" ON public.pending_medical_confirmations
    FOR ALL USING (auth.uid() = user_id);

-- 20. Verified Safety Knowledge Store
CREATE TABLE IF NOT EXISTS public.verified_safety_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type TEXT NOT NULL,
    drug_a TEXT NOT NULL,
    drug_b TEXT,
    condition_name TEXT,
    allergen_class TEXT,
    dosage_form TEXT,
    status TEXT NOT NULL,
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

CREATE POLICY "Public can view verified safety rules" ON public.verified_safety_rules
    FOR SELECT USING (active = true AND verified = true);
CREATE POLICY "Admins can manage verified safety rules" ON public.verified_safety_rules
    FOR ALL USING (auth.role() = 'service_role');

-- 21. Medication Plans (Draft Prescriptions for Professional Review)
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
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_medication_plans_user ON public.medication_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_medication_plans_token ON public.medication_plans(verification_token);
CREATE INDEX IF NOT EXISTS idx_medication_plans_created ON public.medication_plans(created_at DESC);
ALTER TABLE public.medication_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own medication plans" ON public.medication_plans
    FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Public can view valid medication plans via verification token" ON public.medication_plans
    FOR SELECT USING (status = 'active');





