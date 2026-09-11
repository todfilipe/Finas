import { NextResponse } from "next/server";

import { COOKIE_SESSAO } from "@/lib/api";

export async function POST() {
  const redirecionar = new NextResponse(null, { status: 303, headers: { Location: "/login" } });
  redirecionar.cookies.delete(COOKIE_SESSAO);
  return redirecionar;
}
