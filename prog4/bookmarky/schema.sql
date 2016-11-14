DROP TABLE IF EXISTS bm_user CASCADE;
CREATE TABLE bm_user (
  user_id SERIAL PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE CHECK (username ~ '^[a-zA-Z0-9]+$'),
  pw_hash VARCHAR(200) NOT NULL
);

DROP TABLE IF EXISTS bookmark CASCADE;
CREATE TABLE bookmark (
  bookmark_id SERIAL PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES bm_user,
  url VARCHAR(1024) NOT NULL,
  title VARCHAR(1024) NULL,
  notes TEXT NULL,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX bookmark_owner_idx ON bookmark (owner_id);

DROP TABLE IF EXISTS bm_tag CASCADE;
CREATE TABLE bm_tag (
  bookmark_id INTEGER NOT NULL REFERENCES bookmark,
  tag VARCHAR(255) NOT NULL,
  UNIQUE (bookmark_id, tag)
);
CREATE INDEX bm_tag_idx ON bm_tag (tag);

--    Create a new table to store tags, and associate them with IDs. Tags are shared across all users
-- (that is, all users with the tag ‘animal’ use the same tag entity and tag ID for ‘animal’).

--    Modify bm_tag to link bookmarks and tags. There is one small wrinkle we want to support here: users
-- may enter tags with different capitalization, but we want to simplify that for the tag objects. So the bm_tag also
-- needs to have a field for the tag as entered by the user. When a tag is added, bm_tag will get the exact tag, and
-- tag will get the lowercase version of the tag.