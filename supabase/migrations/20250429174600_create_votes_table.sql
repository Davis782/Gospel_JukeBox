-- Migration: Create votes table for song voting results
create table if not exists public.votes (
    id bigserial primary key,
    song_title text not null,
    vote integer not null,
    created_at timestamp with time zone default timezone('utc'::text, now())
);
