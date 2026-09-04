import { redirect } from "next/navigation";

import { criarCategoria } from "@/app/categorias/acoes";
import Cabecalho from "@/components/cabecalho";
import TabelaDeCategorias from "@/components/tabela-de-categorias";
import { pedirApi } from "@/lib/api";
import { lerId } from "@/lib/filtros";
import { formatarDinheiro } from "@/lib/formatar";
import type { Categoria, Utilizador } from "@/lib/tipos";

function somar(categorias: Categoria[]) {
  let total = 0;
  for (const categoria of categorias) {
    total = total + categoria.total_cents;
  }

  return total;
}

export default async function Categorias({ searchParams }: PageProps<"/categorias">) {
  const parametros = await searchParams;
  const aRenomear = lerId(parametros, "renomear");
  const aMesclar = lerId(parametros, "mesclar");
  const erro = typeof parametros.erro === "string" ? parametros.erro : "";

  const [respostaUtilizador, respostaCategorias] = await Promise.all([
    pedirApi("/auth/me"),
    pedirApi("/categories"),
  ]);

  if (!respostaUtilizador.ok || !respostaCategorias.ok) {
    redirect("/login");
  }

  const utilizador: Utilizador = await respostaUtilizador.json();
  const todas: Categoria[] = await respostaCategorias.json();

  const deDespesa = todas.filter((categoria) => categoria.kind === "expense");
  const deReceita = todas.filter((categoria) => categoria.kind === "income");

  const moeda = utilizador.currency_default;

  return (
    <main className="flex flex-1 flex-col">
      <Cabecalho nome={utilizador.name} ativo="categorias" />

      <section className="bg-preto px-6 py-14 md:px-12 md:py-16">
        <div className="mx-auto w-full max-w-6xl">
          <h1 className="font-titulo text-5xl tracking-tight text-branco md:text-7xl">
            Categorias
          </h1>

          <p className="mt-6 text-branco/60">
            {deDespesa.length} de despesas · {deReceita.length} de receitas
          </p>
        </div>
      </section>

      <section className="bg-branco px-6 py-12 md:px-12">
        <div className="mx-auto w-full max-w-6xl">
          <form action={criarCategoria} className="flex flex-wrap items-end gap-4">
            <div className="w-full sm:w-72">
              <label className="block text-xs text-preto/50" htmlFor="nome">
                Categoria nova
              </label>
              <input
                id="nome"
                name="nome"
                maxLength={100}
                required
                placeholder="Ginásio"
                className="mt-2 w-full rounded-full border border-preto/15 bg-branco px-5 py-3 text-sm text-preto placeholder:text-preto/30 focus:border-preto focus:outline-none"
              />
            </div>

            <div className="w-full sm:w-48">
              <label className="block text-xs text-preto/50" htmlFor="tipo">
                Para
              </label>
              <select
                id="tipo"
                name="tipo"
                defaultValue="despesa"
                className="mt-2 w-full rounded-full border border-preto/15 bg-branco px-5 py-3 text-sm text-preto focus:border-preto focus:outline-none"
              >
                <option value="despesa">Despesas</option>
                <option value="receita">Receitas</option>
              </select>
            </div>

            <button
              type="submit"
              className="rounded-full bg-preto px-8 py-3 font-titulo text-sm text-branco transition hover:bg-preto/90"
            >
              Criar
            </button>
          </form>

          {erro ? <p className="mt-6 text-sm text-dourado">{erro}</p> : null}
        </div>
      </section>

      <section className="bg-branco px-6 pb-12 md:px-12">
        <div className="mx-auto w-full max-w-6xl">
          <h2 className="font-titulo text-2xl tracking-tight text-preto md:text-3xl">
            Despesas
          </h2>
          <p className="mt-2 text-sm text-preto/50">
            {formatarDinheiro(somar(deDespesa), moeda)} arrumados
          </p>

          <div className="mt-6">
            <TabelaDeCategorias
              categorias={deDespesa}
              moeda={moeda}
              aRenomear={aRenomear}
              aMesclar={aMesclar}
            />
          </div>
        </div>
      </section>

      <section className="flex-1 bg-branco px-6 pb-20 md:px-12">
        <div className="mx-auto w-full max-w-6xl">
          <h2 className="font-titulo text-2xl tracking-tight text-preto md:text-3xl">
            Receitas
          </h2>
          <p className="mt-2 text-sm text-preto/50">
            {formatarDinheiro(somar(deReceita), moeda)} recebidos
          </p>

          <div className="mt-6">
            <TabelaDeCategorias
              categorias={deReceita}
              moeda={moeda}
              aRenomear={aRenomear}
              aMesclar={aMesclar}
            />
          </div>

          <p className="mt-8 text-sm text-preto/50">
            Só podes apagar categorias sem movimentos. Para as outras, usa mesclar: os movimentos
            passam para a categoria que escolheres, do mesmo tipo.
          </p>
        </div>
      </section>
    </main>
  );
}
