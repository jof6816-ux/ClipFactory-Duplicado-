import { createClient } from "@supabase/supabase-js";
export const browserClient = () =>
  createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
export const adminClient = () =>
  createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!);
// Verifica que quien llama sea admin (token Bearer del usuario).
export async function requireAdmin(req: Request) {
  const token = req.headers.get("authorization")?.replace("Bearer ", "");
  if (!token) return null;
  const admin = adminClient();
  const { data } = await admin.auth.getUser(token);
  if (!data.user) return null;
  const { data: p } = await admin.from("profiles").select("role").eq("id", data.user.id).single();
  return p?.role === "admin" ? admin : null;
}
