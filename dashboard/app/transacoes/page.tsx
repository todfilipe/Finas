import Link from "next/link";
import { redirect } from "next/navigation";

import Cabecalho from "@/components/cabecalho";
import FiltrosDeDespesas from "@/components/filtros-de-despesas";
import TabelaDeDespesas from "@/components/tabela-de-despesas";
import { pedirApi } from "@/lib/api";
import { consultaDaApi, haFiltros, lerFiltros, lerPagina, linkDaPagina } from "@/lib/filtros";
import { formatarDinheiro } from "@/lib/formatar";
import type { ListaDeDespesas, Utilizador } from "@/lib/tipos";

const POR_PAGINA = 50;

export default async function Transacoes({ searchParams }: PageProps<"/transacoes">) {
  const parametros = await searchParams;
  const filtros = lerFiltros(parametros);
  const pagina = lerPagina(parametros);

  const [respostaUtilizador, respostaCategorias, respostaDespesas] = await Promise.all([
    pedirApi("/auth/me"),
    pedirApi("/categories"),
    pedirApi("/expenses?" + consultaDaApi(filtros, POR_PAGINA, pagina)),
  ]);

  if (!respostaUtilizador.ok || !respostaCategorias.ok || !respostaDespesas.ok) {
    redirect("/login");
  }

  const utilizador: Utilizador = await respostaUtilizador.json();
  const categorias: string[] = await respostaCategorias.json();
  const lista: ListaDeDespesas = await respostaDespesas.json();

  const ultimaPagina = Math.max(1, Math.ceil(lista.total / POR_PAGINA));

  return (
    <main className="flex flex-1 flex-col">
      <Cabecalho nome={utilizador.name} ativo="transacoes" />

      <section className="bg-preto px-6 py-14 md:px-12 md:py-16">
        <div className="mx-auto w-full max-w-6xl">
          <h1 className="font-titulo text-5xl tracking-tight text-branco md:text-7xl">
            Transações
          </h1>

          <p className="mt-6 text-branco/60">
            {lista.total} {lista.total === 1 ? "despesa" : "despesas"} ·{" "}
            {formatarDinheiro(lista.total_cents, utilizador.currency_default)}
            {haFiltros(filtros) ? " com estes filtros" : " no total"}
          </p>
        </div>
      </section>

      <section className="bg-branco px-6 py-12 md:px-12">
        <div className="mx-auto w-full max-w-6xl">
          <FiltrosDeDespesas filtros={filtros} categorias={categorias} />
        </div>
      </section>

      <section className="flex-1 bg-branco px-6 pb-20 md:px-12">
        <div className="mx-auto w-full max-w-6xl">
          <TabelaDeDespesas despesas={lista.items} />

          {ultimaPagina > 1 ? (
            <div className="mt-10 flex items-center gap-4">
              {pagina > 1 ? (
                <Link
                  href={linkDaPagina(filtros, pagina - 1)}
                  className="rounded-full border border-preto/15 px-6 py-3 text-sm text-preto transition hover:border-preto"
                >
                  Anterior
                </Link>
              ) : null}

              <span className="text-sm text-preto/50">
                Página {pagina} de {ultimaPagina}
              </span>

              {pagina < ultimaPagina ? (
                <Link
                  href={linkDaPagina(filtros, pagina + 1)}
                  className="rounded-full border border-preto/15 px-6 py-3 text-sm text-preto transition hover:border-preto"
                >
                  Seguinte
                </Link>
              ) : null}
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
