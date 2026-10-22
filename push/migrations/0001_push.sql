CREATE TABLE subscriptions (
 id TEXT PRIMARY KEY,
 endpoint TEXT NOT NULL UNIQUE,
 subscription TEXT NOT NULL,
 preferences TEXT NOT NULL,
 created_at INTEGER NOT NULL,
 updated_at INTEGER NOT NULL,
 revision TEXT NOT NULL
);
CREATE TABLE jobs (
 id TEXT PRIMARY KEY,
 subscription_id TEXT NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
 event_id TEXT NOT NULL,
 event_key TEXT NOT NULL,
 deadline INTEGER NOT NULL,
 due INTEGER NOT NULL,
 expires INTEGER NOT NULL,
 offset_hours INTEGER NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0,
 retry_at INTEGER NOT NULL DEFAULT 0,
 lease_until INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX jobs_due ON jobs(state, retry_at, due);
CREATE INDEX jobs_subscription ON jobs(subscription_id);
CREATE TABLE state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
