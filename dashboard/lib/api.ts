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

export async function enviarApi(caminho: string, metodo: string, corpo?: unknown) {
  const sessao = (await cookies()).get(COOKIE_SESSAO);

  const cabecalhos: Record<string, string> = { "Content-Type": "application/json" };
  if (sessao) {
    cabecalhos.Cookie = COOKIE_SESSAO + "=" + sessao.value;
  }

  return fetch(API_URL + caminho, {
    method: metodo,
    headers: cabecalhos,
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
    cache: "no-store",
  });
}
