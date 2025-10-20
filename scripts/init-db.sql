-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_type AS ENUM ('cold_start', 'new', 'casual', 'active', 'power_user');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ratings_user_id ON ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_ratings_movie_id ON ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_ratings_timestamp ON ratings(timestamp);
CREATE INDEX IF NOT EXISTS idx_movies_genres ON movies USING gin(genres);
CREATE INDEX IF NOT EXISTS idx_movies_title ON movies USING gin(to_tsvector('english', title));

-- Initial data (optional)
-- INSERT INTO ... if you want to pre-populate data