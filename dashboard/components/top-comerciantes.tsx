import { formatarDinheiro } from "@/lib/formatar";
import type { TotalPorComerciante } from "@/lib/tipos";

export default function TopComerciantes({
  comerciantes,
  moeda,
}: {
  comerciantes: TotalPorComerciante[];
  moeda: string;
}) {
  if (comerciantes.length === 0) {
    return <p className="text-preto/50">Nenhuma despesa deste mês tem comerciante associado.</p>;
  }

  return (
    <ul className="flex flex-col">
      {comerciantes.map((comerciante, posicao) => (
        <li
          key={comerciante.merchant}
          className="flex items-baseline justify-between gap-4 border-t border-preto/10 py-5"
        >
          <span className="flex items-baseline gap-4">
            <span className="text-sm text-preto/40">{posicao + 1}</span>
            <span className="font-titulo text-lg tracking-tight text-preto">
              {comerciante.merchant}
            </span>
            <span className="text-sm text-preto/50">
              {comerciante.count} {comerciante.count === 1 ? "vez" : "vezes"}
            </span>
          </span>

          <span className="font-titulo text-lg tracking-tight text-preto">
            {formatarDinheiro(comerciante.total_cents, moeda)}
          </span>
        </li>
      ))}
    </ul>
  );
}
