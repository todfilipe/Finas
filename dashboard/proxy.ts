import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const sessao = request.cookies.get("finas_session");

  if (!sessao) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!login|entrar|sair|_next|favicon.ico).*)"],
};
