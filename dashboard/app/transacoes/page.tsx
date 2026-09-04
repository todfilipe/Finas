import Link from "next/link";
import { redirect } from "next/navigation";

import Cabecalho from "@/components/cabecalho";
import FiltrosDeDespesas from "@/components/filtros-de-despesas";
import TabelaDeDespesas from "@/components/tabela-de-despesas";
import { pedirApi } from "@/lib/api";
import {
  consultaDaApi,
  haFiltros,
  lerFiltros,
  lerId,
  lerPagina,
  linkDaPagina,
} from "@/lib/filtros";
import { formatarDinheiro } from "@/lib/formatar";
import type { Categoria, ListaDeDespesas, Utilizador } from "@/lib/tipos";

const POR_PAGINA = 50;

const ERROS: Record<string, string> = {
  valor: "O valor tem de ser um número maior que zero.",
  data: "A data não está bem escrita.",
  guardar: "Não consegui guardar a despesa. Tenta outra vez.",
  apagar: "Não consegui apagar a despesa. Tenta outra vez.",
};

export default async function Transacoes({ searchParams }: PageProps<"/transacoes">) {
  const parametros = await searchParams;
  const filtros = lerFiltros(parametros);
  const pagina = lerPagina(parametros);
  const aEditar = lerId(parametros, "editar");
  const aApagar = lerId(parametros, "apagar");
  const erro = typeof parametros.erro === "string" ? ERROS[parametros.erro] ?? "" : "";

  const [respostaUtilizador, respostaCategorias, respostaDespesas] = await Promise.all([
    pedirApi("/auth/me"),
    pedirApi("/categories"),
    pedirApi("/expenses?" + consultaDaApi(filtros, POR_PAGINA, pagina)),
  ]);

  if (!respostaUtilizador.ok || !respostaCategorias.ok || !respostaDespesas.ok) {
    redirect("/login");
  }

  const utilizador: Utilizador = await respostaUtilizador.json();
  const lista: ListaDeDespesas = await respostaDespesas.json();
  const moeda = utilizador.currency_default;

  const todas = (await respostaCategorias.json()) as Categoria[];

  const categorias = [];
  const categoriasDeReceita = [];
  for (const categoria of todas) {
    if (categoria.kind === "income") {
      categoriasDeReceita.push(categoria.name);
    } else {
      categorias.push(categoria.name);
    }
  }

  const categoriasDoFiltro =
    filtros.tipo === "receita" ? categoriasDeReceita : categorias;

  const partesDoTotal = [];
  if (lista.income_cents > 0) {
    partesDoTotal.push("Entrou " + formatarDinheiro(lista.income_cents, moeda));
  }
  if (lista.expense_cents > 0) {
    partesDoTotal.push("Saiu " + formatarDinheiro(lista.expense_cents, moeda));
  }
  const resumoDoTotal = partesDoTotal.join(" · ");

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
            {lista.total} {lista.total === 1 ? "movimento" : "movimentos"}
            {haFiltros(filtros) ? " com estes filtros" : ""}
          </p>

          {resumoDoTotal ? <p className="mt-2 text-branco/60">{resumoDoTotal}</p> : null}
        </div>
      </section>

      <section className="bg-branco px-6 py-12 md:px-12">
        <div className="mx-auto w-full max-w-6xl">
          <FiltrosDeDespesas filtros={filtros} categorias={categoriasDoFiltro} />
        </div>
      </section>

      <section className="flex-1 bg-branco px-6 pb-20 md:px-12">
        <div className="mx-auto w-full max-w-6xl">
          {erro && aEditar === 0 ? <p className="mb-6 text-sm text-dourado">{erro}</p> : null}

          <TabelaDeDespesas
            despesas={lista.items}
            categorias={categorias}
            categoriasDeReceita={categoriasDeReceita}
            filtros={filtros}
            pagina={pagina}
            aEditar={aEditar}
            aApagar={aApagar}
            erro={erro}
          />

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
