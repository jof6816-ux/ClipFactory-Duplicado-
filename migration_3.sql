create policy "paid or free users read clips bucket" on storage.objects for select using (
  bucket_id = 'clips' and exists (
    select 1 from profiles p where p.id = auth.uid() and p.active
      and (p.paid or p.free_pass or p.role = 'admin')));
