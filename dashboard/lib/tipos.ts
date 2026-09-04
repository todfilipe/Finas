export type Utilizador = {
  id: number;
  name: string | null;
  timezone: string;
  currency_default: string;
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
  previous_month: string;
  previous_total_cents: number;
  by_category: TotalPorCategoria[];
  top_merchants: TotalPorComerciante[];
};

export type Despesa = {
  id: number;
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
  limit: number;
  offset: number;
  items: Despesa[];
};
