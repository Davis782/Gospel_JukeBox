-- Migration: Create sheet_music table for Gospel JukeBox
CREATE TABLE IF NOT EXISTS sheet_music (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  song_name text NOT NULL,
  label_id uuid REFERENCES labels(id),
  file_path text NOT NULL,
  owner_id uuid REFERENCES users(id),
  upload_date timestamptz DEFAULT now()
);
