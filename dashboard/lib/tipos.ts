export type Utilizador = {
  id: number;
  name: string | null;
  timezone: string;
  currency_default: string;
};

export type Tipo = "expense" | "income";

export type Categoria = {
  id: number;
  name: string;
  kind: Tipo;
  is_default: boolean;
  count: number;
  total_cents: number;
};

export type TotalPorCategoria = {
  category: string;
  total_cents: number;
  count: number;
};

export type TotalPorComerciante = {
  merchant: string;
  total_cents: number;
  count: number;
};

export type TotalPorMes = {
  month: string;
  total_cents: number;
};

export type ResumoDoMes = {
  month: string;
  total_cents: number;
  count: number;
  income_cents: number;
  income_count: number;
  balance_cents: number;
  previous_month: string;
  previous_total_cents: number;
  previous_income_cents: number;
  previous_balance_cents: number;
  by_category: TotalPorCategoria[];
  income_by_category: TotalPorCategoria[];
  top_merchants: TotalPorComerciante[];
};

export type Despesa = {
  id: number;
  kind: Tipo;
  amount_cents: number;
  currency: string;
  category: string | null;
  subcategory: string | null;
  merchant: string | null;
  description: string | null;
  expense_date: string;
  payment_method: string | null;
  created_at: string;
};

export type ListaDeDespesas = {
  total: number;
  total_cents: number;
  expense_cents: number;
  income_cents: number;
  limit: number;
  offset: number;
  items: Despesa[];
};
