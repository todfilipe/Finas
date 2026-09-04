import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { COOKIE_SESSAO } from "@/lib/api";

export async function POST(request: NextRequest) {
  const redirecionar = NextResponse.redirect(new URL("/login", request.url), 303);
  redirecionar.cookies.delete(COOKIE_SESSAO);
  return redirecionar;
}
