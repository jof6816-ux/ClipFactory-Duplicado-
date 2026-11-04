alter table profiles add column if not exists paid boolean not null default false;
alter table profiles add column if not exists free_pass boolean not null default false;
alter table profiles add column if not exists stripe_customer_id text;
create table if not exists publications (
  id uuid primary key default gen_random_uuid(),
  clip_id uuid references clips on delete cascade,
  platform text not null, status text default 'pending' check (status in ('pending','done','failed')),
  external_id text, error text, created_at timestamptz default now(),
  unique (clip_id, platform));
-- Acceso a clips: cuenta activa (no revocada) Y (suscripción pagada O pase gratis O admin)
drop policy if exists "active users see clips" on clips;
create policy "paid or free users see clips" on clips for select using (
  exists (select 1 from profiles p where p.id = auth.uid() and p.active
          and (p.paid or p.free_pass or p.role = 'admin')));
