import Link from "next/link";
import { redirect } from "next/navigation";

import Cabecalho from "@/components/cabecalho";
import GraficoDeCategorias from "@/components/grafico-de-categorias";
import TendenciaMensal from "@/components/tendencia-mensal";
import TopComerciantes from "@/components/top-comerciantes";
import { pedirApi } from "@/lib/api";
import {
  formatarDinheiro,
  mesAnterior,
  mesAtual,
  mesSeguinte,
  mesValido,
  nomeDoMes,
  nomeDoMesSemAno,
} from "@/lib/formatar";
import type { ResumoDoMes, TotalPorMes, Utilizador } from "@/lib/tipos";

function textoDeComparacao(resumo: ResumoDoMes) {
  const anterior = nomeDoMesSemAno(resumo.previous_month);

  if (resumo.previous_total_cents === 0) {
    if (resumo.total_cents === 0) {
      return "";
    }
    return "Nada gasto em " + anterior;
  }

  const diferenca = Math.round(
    ((resumo.total_cents - resumo.previous_total_cents) / resumo.previous_total_cents) * 100
  );

  if (diferenca === 0) {
    return "gastaste o mesmo que em " + anterior;
  }

  if (diferenca > 0) {
    return "gastaste +" + diferenca + "% que em " + anterior;
  }

  return "gastaste " + diferenca + "% que em " + anterior;
}

function comSinal(centimos: number, moeda: string) {
  if (centimos > 0) {
    return "+ " + formatarDinheiro(centimos, moeda);
  }

  return formatarDinheiro(centimos, moeda);
}

export default async function Home({ searchParams }: PageProps<"/">) {
  const parametros = await searchParams;
  const pedido = typeof parametros.mes === "string" ? parametros.mes : "";
  const mes = mesValido(pedido) ? pedido : mesAtual();

  const [respostaUtilizador, respostaResumo, respostaMeses] = await Promise.all([
    pedirApi("/auth/me"),
    pedirApi("/stats/summary?month=" + mes),
    pedirApi("/stats/monthly?months=6&month=" + mes),
  ]);

  if (!respostaUtilizador.ok || !respostaResumo.ok || !respostaMeses.ok) {
    redirect("/login");
  }

  const utilizador: Utilizador = await respostaUtilizador.json();
  const resumo: ResumoDoMes = await respostaResumo.json();
  const meses: TotalPorMes[] = await respostaMeses.json();

  const moeda = utilizador.currency_default;
  const comparacao = textoDeComparacao(resumo);
  const podeAvancar = mes < mesAtual();

  return (
    <main className="flex flex-1 flex-col">
      <Cabecalho nome={utilizador.name} ativo="resumo" />

      <section className="bg-preto px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto w-full max-w-5xl">
          <div className="flex items-center gap-3">
            <Link
              href={"/?mes=" + mesAnterior(mes)}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-branco/20 text-branco transition hover:border-branco"
            >
              ←
            </Link>

            {podeAvancar ? (
              <Link
                href={"/?mes=" + mesSeguinte(mes)}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-branco/20 text-branco transition hover:border-branco"
              >
                →
              </Link>
            ) : (
              <span className="flex h-10 w-10 items-center justify-center rounded-full border border-branco/10 text-branco/20">
                →
              </span>
            )}

            <span className="ml-2 text-branco/50">{nomeDoMes(mes)}</span>
          </div>

          <p className="mt-10 text-branco/50">Saldo do mês</p>
          <p className="mt-2 font-titulo text-6xl tracking-tight text-branco md:text-8xl">
            {comSinal(resumo.balance_cents, moeda)}
          </p>

          <div className="mt-10 flex flex-wrap gap-x-16 gap-y-8">
            <div>
              <p className="text-sm text-branco/50">Entrou</p>
              <p className="mt-1 font-titulo text-2xl text-branco md:text-3xl">
                {formatarDinheiro(resumo.income_cents, moeda)}
              </p>
              <p className="mt-1 text-sm text-branco/40">
                {resumo.income_count} {resumo.income_count === 1 ? "receita" : "receitas"}
              </p>
            </div>

            <div>
              <p className="text-sm text-branco/50">Saiu</p>
              <p className="mt-1 font-titulo text-2xl text-branco md:text-3xl">
                {formatarDinheiro(resumo.total_cents, moeda)}
              </p>
              <p className="mt-1 text-sm text-branco/40">
                {resumo.count} {resumo.count === 1 ? "despesa" : "despesas"}
              </p>
            </div>
          </div>

          {comparacao ? <p className="mt-8 text-branco/60">Este mês {comparacao}.</p> : null}
        </div>
      </section>

      <section className="bg-branco px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto w-full max-w-5xl">
          <h2 className="font-titulo text-3xl tracking-tight text-preto md:text-4xl">
            Onde saiu
          </h2>

          <div className="mt-10">
            <GraficoDeCategorias
              categorias={resumo.by_category}
              total={resumo.total_cents}
              moeda={moeda}
            />
          </div>

          {resumo.income_by_category.length > 0 ? (
            <div className="mt-20">
              <h2 className="font-titulo text-3xl tracking-tight text-preto md:text-4xl">
                Onde entrou
              </h2>

              <div className="mt-10">
                <GraficoDeCategorias
                  categorias={resumo.income_by_category}
                  total={resumo.income_cents}
                  moeda={moeda}
                  singular="receita"
                  plural="receitas"
                />
              </div>
            </div>
          ) : null}
        </div>
      </section>

      <section className="bg-preto px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto w-full max-w-5xl">
          <h2 className="font-titulo text-3xl tracking-tight text-branco md:text-4xl">
            Despesas dos últimos 6 meses
          </h2>

          <div className="mt-12">
            <TendenciaMensal meses={meses} mesAtivo={mes} moeda={moeda} />
          </div>
        </div>
      </section>

      <section className="flex-1 bg-branco px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto w-full max-w-5xl">
          <h2 className="font-titulo text-3xl tracking-tight text-preto md:text-4xl">
            Onde gastaste mais
          </h2>

          <div className="mt-8">
            <TopComerciantes comerciantes={resumo.top_merchants} moeda={moeda} />
          </div>
        </div>
      </section>
    </main>
  );
}
