-- Supabase schema for Noel Whittaker Chatbot
-- Run this in your Supabase SQL editor to create the required tables

-- Conversations table to store chat history
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    user_id TEXT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Index for fast lookups
    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant', 'system'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id
    ON conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at
    ON conversations(created_at DESC);

-- Enable Row Level Security (optional, recommended for production)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Policy to allow users to only access their own conversations
-- Uncomment and modify based on your auth setup
-- CREATE POLICY "Users can access own conversations" ON conversations
--     FOR ALL USING (auth.uid()::text = user_id);
