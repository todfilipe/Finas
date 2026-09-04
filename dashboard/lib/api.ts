import { cookies } from "next/headers";

export const API_URL =
  process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const COOKIE_SESSAO = "finas_session";

export async function pedirApi(caminho: string) {
  const sessao = (await cookies()).get(COOKIE_SESSAO);

  return fetch(API_URL + caminho, {
    headers: sessao ? { Cookie: COOKIE_SESSAO + "=" + sessao.value } : {},
    cache: "no-store",
  });
}
