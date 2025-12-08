-- Drop all tables in reverse order (respecting foreign key constraints)
-- Use with caution - this will delete all data

DROP TABLE IF EXISTS share_urls CASCADE;
DROP TABLE IF EXISTS "column" CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;
