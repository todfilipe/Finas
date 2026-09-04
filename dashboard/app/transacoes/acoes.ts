"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { enviarApi } from "@/lib/api";
import { juntarAoLink } from "@/lib/filtros";

function lerTexto(dados: FormData, nome: string) {
  const valor = dados.get(nome);
  return typeof valor === "string" ? valor.trim() : "";
}

function paraOndeVoltar(dados: FormData) {
  const voltar = lerTexto(dados, "voltar");
  if (voltar.startsWith("/transacoes")) {
    return voltar;
  }

  return "/transacoes";
}

export async function guardarDespesa(dados: FormData) {
  const id = Number(lerTexto(dados, "id"));
  const destino = paraOndeVoltar(dados);
  const voltarAoFormulario = juntarAoLink(destino, "editar=" + id);

  const valor = Number(lerTexto(dados, "valor").replace(",", "."));
  if (!Number.isFinite(valor) || valor <= 0) {
    redirect(juntarAoLink(voltarAoFormulario, "erro=valor"));
  }

  const data = lerTexto(dados, "data");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(data)) {
    redirect(juntarAoLink(voltarAoFormulario, "erro=data"));
  }

  const corpo = {
    amount_cents: Math.round(valor * 100),
    expense_date: data,
    category: lerTexto(dados, "categoria") || null,
    merchant: lerTexto(dados, "comerciante") || null,
    description: lerTexto(dados, "descricao") || null,
  };

  const resposta = await enviarApi("/expenses/" + id, "PATCH", corpo);
  if (!resposta.ok) {
    redirect(juntarAoLink(voltarAoFormulario, "erro=guardar"));
  }

  revalidatePath("/transacoes");
  redirect(destino);
}

export async function apagarDespesa(dados: FormData) {
  const id = Number(lerTexto(dados, "id"));
  const destino = paraOndeVoltar(dados);

  const resposta = await enviarApi("/expenses/" + id, "DELETE");
  if (!resposta.ok) {
    redirect(juntarAoLink(destino, "erro=apagar"));
  }

  revalidatePath("/transacoes");
  redirect(destino);
}
