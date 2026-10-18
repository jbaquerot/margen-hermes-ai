CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES(1);
CREATE TABLE books(
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, author TEXT NOT NULL,
 title_key TEXT NOT NULL, author_key TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(owner,title_key,author_key));
CREATE TABLE reading_state(owner TEXT PRIMARY KEY, book TEXT REFERENCES books(id));
CREATE TABLE notes(
 seq INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT UNIQUE NOT NULL, owner TEXT NOT NULL,
 book TEXT REFERENCES books(id), text TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL);
CREATE INDEX notes_owner_book ON notes(owner,book,created_at,seq);
CREATE TABLE note_versions(
 ref TEXT NOT NULL REFERENCES notes(ref) ON DELETE CASCADE, version INTEGER NOT NULL,
 text TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(ref,version));
CREATE TABLE pending_interactions(owner TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE summaries(
 ref TEXT PRIMARY KEY, owner TEXT NOT NULL, book TEXT NOT NULL REFERENCES books(id),
 mode TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL,
 stale INTEGER NOT NULL DEFAULT 0, coverage TEXT NOT NULL);
CREATE TABLE summary_sources(
 summary TEXT NOT NULL REFERENCES summaries(ref) ON DELETE CASCADE,
 note_ref TEXT NOT NULL, version INTEGER NOT NULL, position INTEGER NOT NULL,
 PRIMARY KEY(summary,note_ref));
CREATE TABLE processed_events(
 key TEXT PRIMARY KEY, owner TEXT NOT NULL, refs TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE outbox(
 event_key TEXT PRIMARY KEY REFERENCES processed_events(key), owner TEXT NOT NULL,
 payload TEXT, sent_parts INTEGER NOT NULL DEFAULT 0, delivered INTEGER NOT NULL DEFAULT 0);
CREATE TABLE jobs(
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL, error TEXT,
 result TEXT);
CREATE TABLE index_jobs(ref TEXT PRIMARY KEY REFERENCES notes(ref) ON DELETE CASCADE, version INTEGER NOT NULL);
CREATE TABLE note_chunks(
 id INTEGER PRIMARY KEY, ref TEXT NOT NULL REFERENCES notes(ref) ON DELETE CASCADE,
 version INTEGER NOT NULL, position INTEGER NOT NULL, UNIQUE(ref,version,position));
CREATE TABLE note_embeddings(
 chunk INTEGER PRIMARY KEY REFERENCES note_chunks(id) ON DELETE CASCADE,
 revision TEXT NOT NULL, vector TEXT NOT NULL);
CREATE TABLE search_sessions(owner TEXT PRIMARY KEY, refs TEXT NOT NULL, cursor INTEGER NOT NULL DEFAULT 0);
CREATE TABLE deletion_ledger(ref TEXT PRIMARY KEY, deleted_at TEXT NOT NULL);
CREATE VIRTUAL TABLE notes_fts USING fts5(ref UNINDEXED, text, tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER note_insert AFTER INSERT ON notes BEGIN
 INSERT INTO notes_fts(ref,text) VALUES(new.ref,new.text);
END;
CREATE TRIGGER note_update AFTER UPDATE OF text ON notes BEGIN
 DELETE FROM notes_fts WHERE ref=old.ref;
 INSERT INTO notes_fts(ref,text) VALUES(new.ref,new.text);
END;
CREATE TRIGGER note_delete AFTER DELETE ON notes BEGIN
 DELETE FROM notes_fts WHERE ref=old.ref;
END;
