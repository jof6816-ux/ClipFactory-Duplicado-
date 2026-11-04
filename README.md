# ClipFactory
1. Supabase: crea proyecto, ejecuta supabase/schema.sql y crea el bucket privado "clips".
2. Registra tu usuario y pon role='admin' en la tabla profiles.
3. Web: cd web && npm i && npm run dev (variables en .env.example).
   Rutas: /login, /join?invite=CODE (registro), /feed (clips), /admin (panel).
4. Agentes: instala ffmpeg, cd workers && pip install -r requirements.txt && python run_all.py
Legal: el buscador solo toma videos Creative Commons y acredita al autor.
Para otro contenido, usa fuentes con permiso escrito (license='authorized').
Monetización: Stripe sobre el acceso de invitados, o clipping autorizado.

## Fase 2: pagos y publicación
- Ejecuta supabase/migration_2.sql.
- Stripe: crea un producto con precio recurrente y pon STRIPE_PRICE_ID. Webhook a /api/stripe/webhook
  (eventos: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted).
  Local: `stripe listen --forward-to localhost:3000/api/stripe/webhook`.
- REQUIRE_PAYMENT=true exige suscripción a los invitados; false les da pase gratis.
- Publicación: PUBLISH_TO activa cada plataforma. Empieza en privado/borrador para probar.
  YouTube: app OAuth con scope youtube.upload. TikTok: app con Content Posting API; sin auditoría
  solo puede publicar en privado. Instagram: cuenta Business + app con instagram_content_publish.
- Publica solo clips con licencia que lo permita (CC BY con crédito) o con permiso del autor.
