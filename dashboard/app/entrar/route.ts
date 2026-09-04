import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { API_URL } from "@/lib/api";

export async function GET(request: NextRequest) {
  const codigo = request.nextUrl.searchParams.get("code") ?? "";

  let resposta;
  try {
    resposta = await fetch(API_URL + "/auth/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: codigo }),
      cache: "no-store",
    });
  } catch {
    return NextResponse.redirect(new URL("/login?erro=servidor", request.url));
  }

  if (resposta.status === 429) {
    return NextResponse.redirect(new URL("/login?erro=tentativas", request.url));
  }

  if (!resposta.ok) {
    return NextResponse.redirect(new URL("/login?erro=codigo", request.url));
  }

  const redirecionar = NextResponse.redirect(new URL("/", request.url));
  for (const cookie of resposta.headers.getSetCookie()) {
    redirecionar.headers.append("set-cookie", cookie);
  }

  return redirecionar;
}
