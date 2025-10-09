-- Initialize LipService database
-- This script runs on first database creation

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search similarity

-- Create initial schema
CREATE SCHEMA IF NOT EXISTS lipservice;

-- Set search path
SET search_path TO lipservice, public;

-- Initial setup complete
SELECT 'LipService database initialized successfully!' AS status;

