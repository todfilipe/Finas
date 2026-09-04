import Link from "next/link";

import type { Filtros } from "@/lib/filtros";

export default function FiltrosDeDespesas({
  filtros,
  categorias,
}: {
  filtros: Filtros;
  categorias: string[];
}) {
  const caixa =
    "mt-2 w-full rounded-full border border-preto/15 bg-branco px-5 py-3 text-sm text-preto placeholder:text-preto/30 focus:border-preto focus:outline-none";
  const etiqueta = "block text-xs text-preto/50";

  return (
    <form method="get" action="/transacoes" className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label className={etiqueta} htmlFor="texto">
            Procurar
          </label>
          <input
            id="texto"
            name="texto"
            defaultValue={filtros.texto}
            placeholder="café, jantar, uber..."
            className={caixa}
          />
        </div>

        <div>
          <label className={etiqueta} htmlFor="tipo">
            Tipo
          </label>
          <select id="tipo" name="tipo" defaultValue={filtros.tipo} className={caixa}>
            <option value="">Tudo</option>
            <option value="despesa">Despesas</option>
            <option value="receita">Receitas</option>
          </select>
        </div>

        <div>
          <label className={etiqueta} htmlFor="categoria">
            Categoria
          </label>
          <select id="categoria" name="categoria" defaultValue={filtros.categoria} className={caixa}>
            <option value="">Todas</option>
            {categorias.map((categoria) => (
              <option key={categoria} value={categoria}>
                {categoria}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={etiqueta} htmlFor="comerciante">
            Comerciante
          </label>
          <input
            id="comerciante"
            name="comerciante"
            defaultValue={filtros.comerciante}
            placeholder="Continente"
            className={caixa}
          />
        </div>

        <div>
          <label className={etiqueta} htmlFor="de">
            De
          </label>
          <input id="de" name="de" type="date" defaultValue={filtros.de} className={caixa} />
        </div>

        <div>
          <label className={etiqueta} htmlFor="ate">
            Até
          </label>
          <input id="ate" name="ate" type="date" defaultValue={filtros.ate} className={caixa} />
        </div>

        <div>
          <label className={etiqueta} htmlFor="min">
            Valor mínimo
          </label>
          <input
            id="min"
            name="min"
            type="number"
            min="0"
            step="0.01"
            defaultValue={filtros.min}
            placeholder="0"
            className={caixa}
          />
        </div>

        <div>
          <label className={etiqueta} htmlFor="max">
            Valor máximo
          </label>
          <input
            id="max"
            name="max"
            type="number"
            min="0"
            step="0.01"
            defaultValue={filtros.max}
            placeholder="sem limite"
            className={caixa}
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          type="submit"
          className="rounded-full bg-preto px-8 py-3 font-titulo text-sm text-branco transition hover:bg-preto/90"
        >
          Filtrar
        </button>

        <Link href="/transacoes" className="text-sm text-preto/50 transition hover:text-preto">
          Limpar
        </Link>
      </div>
    </form>
  );
}
