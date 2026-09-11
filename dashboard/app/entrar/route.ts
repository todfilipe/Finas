import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { API_URL } from "@/lib/api";

function irPara(caminho: string) {
  return new NextResponse(null, { status: 307, headers: { Location: caminho } });
}

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
    return irPara("/login?erro=servidor");
  }

  if (resposta.status === 429) {
    return irPara("/login?erro=tentativas");
  }

  if (!resposta.ok) {
    return irPara("/login?erro=codigo");
  }

  const redirecionar = irPara("/");
  for (const cookie of resposta.headers.getSetCookie()) {
    redirecionar.headers.append("set-cookie", cookie);
  }

  return redirecionar;
}
