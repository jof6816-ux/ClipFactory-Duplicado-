# Despliegue

## 1. Supabase (base de datos, login, archivos)
1. Crea el proyecto en supabase.com.
2. SQL Editor: ejecuta en orden: schema.sql, migration_2.sql y migration_3.sql (después de crear el bucket "clips").
3. Storage: crea el bucket PRIVADO "clips".
4. Authentication > Providers: deja Email activo (desactiva "Confirm email", ya se confirma por API).
5. Crea tu cuenta (en Authentication > Users > Add user) y en la tabla profiles inserta
   tu fila con role='admin', active=true.
6. Copia: Project URL, anon key y service_role key (esta última NUNCA en el navegador).

## 2. Web en Vercel
1. Sube la carpeta a GitHub. En vercel.com > Add New Project, elige el repo.
2. Root Directory: web
3. Variables de entorno: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY,
   SUPABASE_SERVICE_KEY, STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET, REQUIRE_PAYMENT.
4. Deploy. Tu dominio queda en tu-proyecto.vercel.app (puedes conectar uno propio).

## 3. Webhook de Stripe
Dashboard > Developers > Webhooks > Add endpoint:
https://TU-DOMINIO/api/stripe/webhook
Eventos: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted.
Copia el "Signing secret" a STRIPE_WEBHOOK_SECRET en Vercel y redespliega.

## 4. Agentes en un servidor (Railway, Render o Fly.io)
Vercel no sirve para esto (FFmpeg y procesos largos), usa un servicio de "worker":
1. Nuevo servicio desde el repo, Root Directory: workers (detecta el Dockerfile).
2. Tipo: Background Worker (sin puerto).
3. Variables: SUPABASE_URL, SUPABASE_SERVICE_KEY, YOUTUBE_API_KEY, QUERIES,
   PUBLISH_TO y las claves de cada plataforma (ver .env.example).
4. Recursos: mínimo 1 GB de RAM. Los clips se procesan en disco temporal.
Prueba local antes: docker build -t agents workers && docker run --env-file .env agents

## 5. Lista de verificación
- [ ] Entras a /login con tu admin y llegas a /admin
- [ ] "Crear invitación" genera un enlace; en ventana privada te registras
- [ ] Un clip aparece en /feed tras correr los agentes
- [ ] "Eliminar acceso" bloquea al invitado y su login falla
- [ ] Pago de prueba con tarjeta 4242 4242 4242 4242 activa el acceso
- [ ] Publicación en modo privado en cada plataforma antes de abrirla
- [ ] Rota la service_role key si alguna vez se filtra
