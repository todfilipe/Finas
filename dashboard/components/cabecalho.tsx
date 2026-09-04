import Link from "next/link";

export default function Cabecalho({
  nome,
  ativo,
}: {
  nome: string | null;
  ativo: "resumo" | "transacoes";
}) {
  const normal = "text-sm text-preto/50 transition hover:text-preto";
  const selecionado = "text-sm text-preto";

  return (
    <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-4 bg-branco px-6 py-6 md:px-12">
      <div className="flex items-center gap-5 sm:gap-8">
        <p className="font-titulo text-2xl tracking-tight text-preto">
          Finas<span className="text-dourado">.</span>
        </p>

        <nav className="flex items-center gap-4 sm:gap-6">
          <Link href="/" className={ativo === "resumo" ? selecionado : normal}>
            Resumo
          </Link>
          <Link href="/transacoes" className={ativo === "transacoes" ? selecionado : normal}>
            Transações
          </Link>
        </nav>
      </div>

      <div className="ml-auto flex items-center gap-5">
        {nome ? <span className="hidden text-sm text-preto/50 sm:block">{nome}</span> : null}

        <form action="/sair" method="post">
          <button
            type="submit"
            className="rounded-full border border-preto/15 px-5 py-2 text-sm text-preto transition hover:border-preto"
          >
            Sair
          </button>
        </form>
      </div>
    </header>
  );
}
