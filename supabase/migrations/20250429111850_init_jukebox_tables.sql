-- enable UUID generation
create extension if not exists "uuid-ossp";

-- users table
create table if not exists users (
  id uuid primary key default uuid_generate_v4(),
  username text unique not null,
  password_hash text not null,
  role text not null
);

-- labels table
create table if not exists labels (
  id uuid primary key default uuid_generate_v4(),
  song_title text not null,
  instrument text not null,
  name text not null,
  owner_id uuid references users(id)
);

-- notes table
create table if not exists notes (
  id uuid primary key default uuid_generate_v4(),
  song_title text not null,
  content text not null,
  label_id uuid references labels(id),
  owner_id uuid references users(id),
  created_at timestamptz default now()
);