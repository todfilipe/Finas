import Link from "next/link";

import { apagarDespesa } from "@/app/transacoes/acoes";
import FormularioDeDespesa from "@/components/formulario-de-despesa";
import type { Filtros } from "@/lib/filtros";
import { linkDaLinha, linkDaPagina } from "@/lib/filtros";
import { formatarData, formatarDinheiro } from "@/lib/formatar";
import type { Despesa } from "@/lib/tipos";

function valorDaLinha(despesa: Despesa) {
  const valor = formatarDinheiro(despesa.amount_cents, despesa.currency);
  return despesa.kind === "income" ? "+ " + valor : valor;
}

export default function TabelaDeDespesas({
  despesas,
  categorias,
  categoriasDeReceita,
  filtros,
  pagina,
  aEditar,
  aApagar,
  erro,
}: {
  despesas: Despesa[];
  categorias: string[];
  categoriasDeReceita: string[];
  filtros: Filtros;
  pagina: number;
  aEditar: number;
  aApagar: number;
  erro: string;
}) {
  if (despesas.length === 0) {
    return <p className="py-10 text-preto/50">Nenhum movimento corresponde a estes filtros.</p>;
  }

  const voltar = linkDaPagina(filtros, pagina);

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-3xl border-collapse text-left">
        <thead>
          <tr className="border-b border-preto/15 text-xs text-preto/50">
            <th className="py-4 pr-4 font-normal">Data</th>
            <th className="py-4 pr-4 font-normal">Descrição</th>
            <th className="hidden py-4 pr-4 font-normal sm:table-cell">Categoria</th>
            <th className="hidden py-4 pr-4 font-normal sm:table-cell">Comerciante</th>
            <th className="py-4 pl-4 text-right font-normal">Valor</th>
            <th className="py-4 pl-4 text-right font-normal"></th>
          </tr>
        </thead>

        <tbody>
          {despesas.map((despesa) =>
            despesa.id === aEditar ? (
              <tr key={despesa.id} className="border-b border-preto/10">
                <td colSpan={6}>
                  <FormularioDeDespesa
                    despesa={despesa}
                    categorias={despesa.kind === "income" ? categoriasDeReceita : categorias}
                    voltar={voltar}
                    erro={erro}
                  />
                </td>
              </tr>
            ) : (
              <tr key={despesa.id} className="border-b border-preto/10 align-top">
                <td className="py-5 pr-4 text-sm whitespace-nowrap text-preto/60">
                  {formatarData(despesa.expense_date)}
                </td>

                <td className="py-5 pr-4 text-sm text-preto">
                  {despesa.description ? despesa.description : "Sem descrição"}
                  <span className="mt-1 block text-xs text-preto/50 sm:hidden">
                    {despesa.kind === "income" ? "Receita · " : ""}
                    {despesa.category ? despesa.category : "Sem categoria"}
                    {despesa.merchant ? " · " + despesa.merchant : ""}
                  </span>
                </td>

                <td className="hidden py-5 pr-4 sm:table-cell">
                  <span
                    className={
                      "rounded-full px-3 py-1 text-xs whitespace-nowrap " +
                      (despesa.kind === "income"
                        ? "border border-dourado/40 text-dourado"
                        : "border border-preto/15 text-preto/70")
                    }
                  >
                    {despesa.category ? despesa.category : "Sem categoria"}
                  </span>
                </td>

                <td className="hidden py-5 pr-4 text-sm text-preto/60 sm:table-cell">
                  {despesa.merchant ? despesa.merchant : ""}
                </td>

                <td
                  className={
                    "py-5 pl-4 text-right font-titulo text-base whitespace-nowrap " +
                    (despesa.kind === "income" ? "text-dourado" : "text-preto")
                  }
                >
                  {valorDaLinha(despesa)}
                </td>

                <td className="py-5 pl-4 text-right whitespace-nowrap">
                  {despesa.id === aApagar ? (
                    <form action={apagarDespesa} className="flex items-center justify-end gap-3">
                      <input type="hidden" name="id" value={despesa.id} />
                      <input type="hidden" name="voltar" value={voltar} />

                      <span className="hidden text-xs text-preto/50 md:inline">Apagar mesmo?</span>

                      <button
                        type="submit"
                        className="rounded-full bg-preto px-4 py-2 text-xs text-branco transition hover:bg-preto/90"
                      >
                        Apagar
                      </button>

                      <Link
                        href={voltar}
                        className="text-xs text-preto/50 transition hover:text-preto"
                      >
                        Não
                      </Link>
                    </form>
                  ) : (
                    <span className="flex items-center justify-end gap-4">
                      <Link
                        href={linkDaLinha(filtros, pagina, "editar", despesa.id)}
                        className="text-xs text-preto/50 transition hover:text-preto"
                      >
                        Editar
                      </Link>

                      <Link
                        href={linkDaLinha(filtros, pagina, "apagar", despesa.id)}
                        className="text-xs text-preto/50 transition hover:text-preto"
                      >
                        Apagar
                      </Link>
                    </span>
                  )}
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>
    </div>
  );
}
