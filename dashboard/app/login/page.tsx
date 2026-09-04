import { redirect } from "next/navigation";

const ERROS: Record<string, string> = {
  codigo: "Esse código já não serve. Escreve /dashboard ao Finas para receberes outro.",
  tentativas: "Demasiadas tentativas. Espera uns minutos antes de tentar outra vez.",
  servidor: "Não consegui falar com o servidor. Tenta daqui a pouco.",
};

export default async function PaginaDeLogin({ searchParams }: PageProps<"/login">) {
  const parametros = await searchParams;

  const codigo = typeof parametros.code === "string" ? parametros.code : "";
  if (codigo) {
    redirect("/entrar?code=" + encodeURIComponent(codigo));
  }

  const erro = typeof parametros.erro === "string" ? ERROS[parametros.erro] : "";

  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-preto px-6 py-20">
      <div className="w-full max-w-sm">
        <p className="font-titulo text-5xl tracking-tight text-branco">
          Finas<span className="text-dourado">.</span>
        </p>
        <p className="mt-4 text-branco/60">
          Escreve <span className="text-branco">/dashboard</span> ao bot no Telegram e usa aqui o
          código que ele te enviar.
        </p>

        <form action="/entrar" method="get" className="mt-12">
          <label htmlFor="code" className="block text-sm text-branco/60">
            Código de acesso
          </label>

          <input
            id="code"
            name="code"
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength={6}
            autoComplete="one-time-code"
            placeholder="000000"
            required
            autoFocus
            className="mt-3 w-full rounded-3xl border border-branco/20 bg-transparent px-6 py-5 text-center font-titulo text-4xl tracking-[0.3em] text-branco placeholder:text-branco/20 focus:border-branco focus:outline-none"
          />

          {erro ? <p className="mt-4 text-sm text-branco/70">{erro}</p> : null}

          <button
            type="submit"
            className="mt-6 w-full rounded-full bg-branco px-8 py-4 font-titulo text-base text-preto transition hover:bg-branco/90"
          >
            Entrar
          </button>
        </form>
      </div>
    </main>
  );
}
