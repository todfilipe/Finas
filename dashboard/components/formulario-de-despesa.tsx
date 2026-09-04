import Link from "next/link";

import { guardarDespesa } from "@/app/transacoes/acoes";
import type { Despesa } from "@/lib/tipos";

const CAIXA =
  "mt-2 w-full rounded-full border border-preto/15 bg-branco px-5 py-3 text-sm text-preto placeholder:text-preto/30 focus:border-preto focus:outline-none";
const ETIQUETA = "block text-xs text-preto/50";

export default function FormularioDeDespesa({
  despesa,
  categorias,
  voltar,
  erro,
}: {
  despesa: Despesa;
  categorias: string[];
  voltar: string;
  erro: string;
}) {
  return (
    <form action={guardarDespesa} className="flex flex-col gap-6 py-6">
      <input type="hidden" name="id" value={despesa.id} />
      <input type="hidden" name="voltar" value={voltar} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div>
          <label className={ETIQUETA} htmlFor={"data-" + despesa.id}>
            Data
          </label>
          <input
            id={"data-" + despesa.id}
            name="data"
            type="date"
            required
            defaultValue={despesa.expense_date}
            className={CAIXA}
          />
        </div>

        <div>
          <label className={ETIQUETA} htmlFor={"valor-" + despesa.id}>
            {despesa.kind === "income" ? "Recebido" : "Valor"} ({despesa.currency})
          </label>
          <input
            id={"valor-" + despesa.id}
            name="valor"
            type="number"
            min="0.01"
            step="0.01"
            required
            defaultValue={(despesa.amount_cents / 100).toFixed(2)}
            className={CAIXA}
          />
        </div>

        <div>
          <label className={ETIQUETA} htmlFor={"categoria-" + despesa.id}>
            Categoria
          </label>
          <select
            id={"categoria-" + despesa.id}
            name="categoria"
            defaultValue={despesa.category ?? ""}
            className={CAIXA}
          >
            <option value="">Sem categoria</option>
            {categorias.map((categoria) => (
              <option key={categoria} value={categoria}>
                {categoria}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={ETIQUETA} htmlFor={"comerciante-" + despesa.id}>
            Comerciante
          </label>
          <input
            id={"comerciante-" + despesa.id}
            name="comerciante"
            defaultValue={despesa.merchant ?? ""}
            placeholder="Continente"
            className={CAIXA}
          />
        </div>

        <div>
          <label className={ETIQUETA} htmlFor={"descricao-" + despesa.id}>
            Descrição
          </label>
          <input
            id={"descricao-" + despesa.id}
            name="descricao"
            defaultValue={despesa.description ?? ""}
            placeholder="almoço"
            className={CAIXA}
          />
        </div>
      </div>

      {erro ? <p className="text-sm text-dourado">{erro}</p> : null}

      <div className="flex items-center gap-4">
        <button
          type="submit"
          className="rounded-full bg-preto px-8 py-3 font-titulo text-sm text-branco transition hover:bg-preto/90"
        >
          Guardar
        </button>

        <Link href={voltar} className="text-sm text-preto/50 transition hover:text-preto">
          Cancelar
        </Link>
      </div>
    </form>
  );
}
