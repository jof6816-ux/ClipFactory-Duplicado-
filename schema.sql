create table profiles (
  id uuid primary key references auth.users on delete cascade,
  email text, role text not null default 'guest', active boolean not null default true,
  created_at timestamptz default now());
create table invites (
  code text primary key, created_by uuid, used_by uuid, created_at timestamptz default now());
create table sources (
  id serial primary key, platform text, channel_id text, authorized boolean default false, note text);
create table videos (
  id uuid primary key default gen_random_uuid(),
  platform text, source_url text unique, title text, author text,
  license text, views bigint, status text default 'found'
    check (status in ('found','editing','edited','published','failed')),
  raw_path text, clip_path text, error text, created_at timestamptz default now());
create table clips (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos on delete cascade,
  storage_path text, credit text, start_s int, end_s int, published_at timestamptz default now());

alter table profiles enable row level security;
alter table clips enable row level security;
create policy "own profile" on profiles for select using (auth.uid() = id);
create policy "active users see clips" on clips for select using (
  exists (select 1 from profiles p where p.id = auth.uid() and p.active));
-- Crea un bucket privado llamado "clips" en Storage.
-- Tu cuenta admin: inserta en profiles con role='admin'.
