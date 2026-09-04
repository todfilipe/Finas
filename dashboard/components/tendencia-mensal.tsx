import { formatarDinheiroCurto, nomeCurtoDoMes, percentagem } from "@/lib/formatar";
import type { TotalPorMes } from "@/lib/tipos";

export default function TendenciaMensal({
  meses,
  mesAtivo,
  moeda,
}: {
  meses: TotalPorMes[];
  mesAtivo: string;
  moeda: string;
}) {
  let maior = 0;
  for (const mes of meses) {
    if (mes.total_cents > maior) {
      maior = mes.total_cents;
    }
  }

  if (maior === 0) {
    return <p className="text-branco/50">Ainda não há despesas nestes meses.</p>;
  }

  return (
    <div className="flex items-end gap-2 sm:gap-4">
      {meses.map((mes) => (
        <div key={mes.month} className="flex flex-1 flex-col items-center">
          <span className="mb-3 text-[11px] text-branco/50 sm:text-xs">
            {mes.total_cents > 0 ? formatarDinheiroCurto(mes.total_cents, moeda) : ""}
          </span>

          <div className="flex h-40 w-full items-end sm:h-56">
            <div
              className={
                "min-h-1 w-full rounded-t-2xl " +
                (mes.month === mesAtivo ? "bg-branco" : "bg-branco/20")
              }
              style={{ height: percentagem(mes.total_cents, maior) + "%" }}
            />
          </div>

          <span
            className={
              "mt-4 text-xs sm:text-sm " +
              (mes.month === mesAtivo ? "text-branco" : "text-branco/50")
            }
          >
            {nomeCurtoDoMes(mes.month)}
          </span>
        </div>
      ))}
    </div>
  );
}
