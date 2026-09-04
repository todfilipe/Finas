import { formatarDinheiro, percentagem } from "@/lib/formatar";
import type { TotalPorCategoria } from "@/lib/tipos";

export default function GraficoDeCategorias({
  categorias,
  total,
  moeda,
}: {
  categorias: TotalPorCategoria[];
  total: number;
  moeda: string;
}) {
  if (categorias.length === 0) {
    return <p className="text-preto/50">Ainda não há despesas neste mês.</p>;
  }

  let maior = 0;
  for (const categoria of categorias) {
    if (categoria.total_cents > maior) {
      maior = categoria.total_cents;
    }
  }

  return (
    <div className="flex flex-col gap-7">
      {categorias.map((categoria) => (
        <div key={categoria.category}>
          <div className="flex items-baseline justify-between gap-4">
            <span className="font-titulo text-lg tracking-tight text-preto">
              {categoria.category}
            </span>
            <span className="font-titulo text-lg tracking-tight text-preto">
              {formatarDinheiro(categoria.total_cents, moeda)}
            </span>
          </div>

          <div className="mt-3 h-2 w-full rounded-full bg-preto/10">
            <div
              className="h-2 rounded-full bg-preto"
              style={{ width: percentagem(categoria.total_cents, maior) + "%" }}
            />
          </div>

          <p className="mt-2 text-sm text-preto/50">
            {percentagem(categoria.total_cents, total)}% do mês · {categoria.count}{" "}
            {categoria.count === 1 ? "despesa" : "despesas"}
          </p>
        </div>
      ))}
    </div>
  );
}
