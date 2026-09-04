import { formatarData, formatarDinheiro } from "@/lib/formatar";
import type { Despesa } from "@/lib/tipos";

export default function TabelaDeDespesas({ despesas }: { despesas: Despesa[] }) {
  if (despesas.length === 0) {
    return <p className="py-10 text-preto/50">Nenhuma despesa corresponde a estes filtros.</p>;
  }

  return (
    <table className="w-full border-collapse text-left">
      <thead>
        <tr className="border-b border-preto/15 text-xs text-preto/50">
          <th className="py-4 pr-4 font-normal">Data</th>
          <th className="py-4 pr-4 font-normal">Descrição</th>
          <th className="hidden py-4 pr-4 font-normal sm:table-cell">Categoria</th>
          <th className="hidden py-4 pr-4 font-normal sm:table-cell">Comerciante</th>
          <th className="py-4 pl-4 text-right font-normal">Valor</th>
        </tr>
      </thead>

      <tbody>
        {despesas.map((despesa) => (
          <tr key={despesa.id} className="border-b border-preto/10 align-top">
            <td className="py-5 pr-4 text-sm whitespace-nowrap text-preto/60">
              {formatarData(despesa.expense_date)}
            </td>

            <td className="py-5 pr-4 text-sm text-preto">
              {despesa.description ? despesa.description : "Sem descrição"}
              <span className="mt-1 block text-xs text-preto/50 sm:hidden">
                {despesa.category ? despesa.category : "Sem categoria"}
                {despesa.merchant ? " · " + despesa.merchant : ""}
              </span>
            </td>

            <td className="hidden py-5 pr-4 sm:table-cell">
              <span className="rounded-full border border-preto/15 px-3 py-1 text-xs whitespace-nowrap text-preto/70">
                {despesa.category ? despesa.category : "Sem categoria"}
              </span>
            </td>

            <td className="hidden py-5 pr-4 text-sm text-preto/60 sm:table-cell">
              {despesa.merchant ? despesa.merchant : ""}
            </td>

            <td className="py-5 pl-4 text-right font-titulo text-base whitespace-nowrap text-preto">
              {formatarDinheiro(despesa.amount_cents, despesa.currency)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
