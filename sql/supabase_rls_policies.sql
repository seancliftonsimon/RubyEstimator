-- Supabase RLS policy and index templates for RubyEstimator
--
-- This app uses a single server-side connection (DATABASE_URL). For Supabase with RLS enabled,
-- use the service role connection string so the app bypasses RLS; the app enforces admin vs
-- user permissions in code.
--
-- If you instead use a role that is subject to RLS (e.g. authenticated API access), adapt
-- these policies. The app uses integer user id (users.id); Supabase Auth uses auth.uid() (UUID).
-- You would need to map auth.uid() to users.id (e.g. via a table or JWT claim) for policies
-- that filter by "own rows".

-- Indexes used by RLS policies (create if not exist)
CREATE INDEX IF NOT EXISTS idx_runs_user_started_at ON runs(user_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_vehicle_key ON runs(vehicle_key);
CREATE INDEX IF NOT EXISTS idx_runs_bought_at ON runs(bought_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Example RLS policies (enable RLS first: ALTER TABLE runs ENABLE ROW LEVEL SECURITY; etc.)
-- These are templates; adjust role names and conditions to match your Supabase Auth setup.

-- runs: users can SELECT/INSERT/UPDATE their own rows (user_id = current app user); no DELETE for regular users
-- Admins (e.g. JWT claim user_role = 'admin') can SELECT/INSERT/UPDATE/DELETE all.
-- Replace :app_user_id with your way of passing current user (e.g. current_setting('app.user_id')::int).

-- Example for runs (if using session variable set by app):
-- CREATE POLICY runs_select_own ON runs FOR SELECT USING (user_id = current_setting('app.user_id', true)::int);
-- CREATE POLICY runs_insert_own ON runs FOR INSERT WITH CHECK (user_id = current_setting('app.user_id', true)::int);
-- CREATE POLICY runs_update_own ON runs FOR UPDATE USING (user_id = current_setting('app.user_id', true)::int);
-- CREATE POLICY runs_admin_all ON runs FOR ALL USING (current_setting('app.user_role', true) = 'admin');

-- Reference/catalog tables (ref_makes, ref_models, ref_aliases): typically SELECT for all;
-- INSERT/UPDATE/DELETE only for admin or service role. Public SELECT often needed for dropdowns.
-- CREATE POLICY ref_makes_select ON ref_makes FOR SELECT USING (true);
-- CREATE POLICY ref_makes_admin ON ref_makes FOR ALL USING (current_setting('app.user_role', true) = 'admin');

-- vehicles, field_values, evidence: app creates/updates these during resolution; restrict by run ownership
-- or allow service role only for writes.
-- users: SELECT own row for login; admin can SELECT/INSERT/UPDATE (no DELETE for regular admin, or restrict).

-- app_config, cat_prices: admin or service role only for write; SELECT for app role.
-- CREATE POLICY app_config_select ON app_config FOR SELECT USING (true);
-- CREATE POLICY app_config_admin ON app_config FOR ALL USING (current_setting('app.user_role', true) = 'admin');
