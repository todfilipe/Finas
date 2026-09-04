import Link from "next/link";

import { apagarCategoria, mesclarCategoria, renomearCategoria } from "@/app/categorias/acoes";
import { formatarDinheiro } from "@/lib/formatar";
import type { Categoria } from "@/lib/tipos";

const CAIXA =
  "w-full rounded-full border border-preto/15 bg-branco px-5 py-3 text-sm text-preto placeholder:text-preto/30 focus:border-preto focus:outline-none";

function LinhaARenomear({ categoria }: { categoria: Categoria }) {
  return (
    <form action={renomearCategoria} className="flex flex-wrap items-center gap-4 py-4">
      <input type="hidden" name="id" value={categoria.id} />

      <input
        name="nome"
        defaultValue={categoria.name}
        maxLength={100}
        required
        autoFocus
        className={CAIXA + " sm:w-72"}
      />

      <button
        type="submit"
        className="rounded-full bg-preto px-6 py-3 font-titulo text-sm text-branco transition hover:bg-preto/90"
      >
        Guardar
      </button>

      <Link href="/categorias" className="text-sm text-preto/50 transition hover:text-preto">
        Cancelar
      </Link>
    </form>
  );
}

function LinhaAMesclar({
  categoria,
  categorias,
}: {
  categoria: Categoria;
  categorias: Categoria[];
}) {
  const outras = categorias.filter(
    (uma) => uma.id !== categoria.id && uma.kind === categoria.kind
  );

  if (outras.length === 0) {
    return (
      <p className="py-4 text-sm text-preto/50">
        Precisas de ter outra categoria do mesmo tipo para poder mesclar esta.
      </p>
    );
  }

  return (
    <form action={mesclarCategoria} className="flex flex-wrap items-center gap-4 py-4">
      <input type="hidden" name="id" value={categoria.id} />

      <span className="text-sm text-preto/60">
        Passar {categoria.kind === "income" ? "as receitas" : "as despesas"} de {categoria.name}{" "}
        para
      </span>

      <select name="destino" defaultValue={outras[0].id} className={CAIXA + " sm:w-64"}>
        {outras.map((outra) => (
          <option key={outra.id} value={outra.id}>
            {outra.name}
          </option>
        ))}
      </select>

      <button
        type="submit"
        className="rounded-full bg-preto px-6 py-3 font-titulo text-sm text-branco transition hover:bg-preto/90"
      >
        Mesclar
      </button>

      <Link href="/categorias" className="text-sm text-preto/50 transition hover:text-preto">
        Cancelar
      </Link>
    </form>
  );
}

export default function TabelaDeCategorias({
  categorias,
  moeda,
  aRenomear,
  aMesclar,
}: {
  categorias: Categoria[];
  moeda: string;
  aRenomear: number;
  aMesclar: number;
}) {
  if (categorias.length === 0) {
    return <p className="py-10 text-preto/50">Ainda não tens nenhuma categoria.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-2xl border-collapse text-left">
        <thead>
          <tr className="border-b border-preto/15 text-xs text-preto/50">
            <th className="py-4 pr-4 font-normal">Categoria</th>
            <th className="py-4 pr-4 text-right font-normal">Movimentos</th>
            <th className="py-4 pl-4 text-right font-normal">Total</th>
            <th className="py-4 pl-4 text-right font-normal"></th>
          </tr>
        </thead>

        <tbody>
          {categorias.map((categoria) =>
            categoria.id === aRenomear || categoria.id === aMesclar ? (
              <tr key={categoria.id} className="border-b border-preto/10">
                <td colSpan={4}>
                  {categoria.id === aRenomear ? (
                    <LinhaARenomear categoria={categoria} />
                  ) : (
                    <LinhaAMesclar categoria={categoria} categorias={categorias} />
                  )}
                </td>
              </tr>
            ) : (
              <tr key={categoria.id} className="border-b border-preto/10">
                <td className="py-5 pr-4 text-sm text-preto">{categoria.name}</td>

                <td className="py-5 pr-4 text-right text-sm whitespace-nowrap text-preto/60">
                  {categoria.count}
                </td>

                <td className="py-5 pl-4 text-right font-titulo text-base whitespace-nowrap text-preto">
                  {formatarDinheiro(categoria.total_cents, moeda)}
                </td>

                <td className="py-5 pl-4 text-right whitespace-nowrap">
                  <span className="flex items-center justify-end gap-4">
                    <Link
                      href={"/categorias?renomear=" + categoria.id}
                      className="text-xs text-preto/50 transition hover:text-preto"
                    >
                      Renomear
                    </Link>

                    <Link
                      href={"/categorias?mesclar=" + categoria.id}
                      className="text-xs text-preto/50 transition hover:text-preto"
                    >
                      Mesclar
                    </Link>

                    {categoria.count === 0 ? (
                      <form action={apagarCategoria}>
                        <input type="hidden" name="id" value={categoria.id} />
                        <button
                          type="submit"
                          className="text-xs text-preto/50 transition hover:text-preto"
                        >
                          Apagar
                        </button>
                      </form>
                    ) : null}
                  </span>
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>
    </div>
  );
}
