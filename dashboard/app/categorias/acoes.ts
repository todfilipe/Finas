"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { enviarApi } from "@/lib/api";
import { juntarAoLink } from "@/lib/filtros";

function lerTexto(dados: FormData, nome: string) {
  const valor = dados.get(nome);
  return typeof valor === "string" ? valor.trim() : "";
}

async function lerErro(resposta: Response) {
  try {
    const corpo = await resposta.json();
    if (typeof corpo.detail === "string") {
      return corpo.detail;
    }
  } catch {
    return "Algo correu mal. Tenta outra vez.";
  }

  return "Algo correu mal. Tenta outra vez.";
}

function paraOndeVoltar(erro: string, aberta?: string) {
  let destino = "/categorias";
  if (aberta) {
    destino = juntarAoLink(destino, aberta);
  }
  if (erro) {
    destino = juntarAoLink(destino, "erro=" + encodeURIComponent(erro));
  }

  return destino;
}

export async function criarCategoria(dados: FormData) {
  const nome = lerTexto(dados, "nome");
  const tipo = lerTexto(dados, "tipo") === "receita" ? "income" : "expense";

  const resposta = await enviarApi("/categories", "POST", { name: nome, kind: tipo });
  if (!resposta.ok) {
    redirect(paraOndeVoltar(await lerErro(resposta)));
  }

  revalidatePath("/categorias");
  redirect("/categorias");
}

export async function renomearCategoria(dados: FormData) {
  const id = Number(lerTexto(dados, "id"));
  const nome = lerTexto(dados, "nome");

  const resposta = await enviarApi("/categories/" + id, "PATCH", { name: nome });
  if (!resposta.ok) {
    redirect(paraOndeVoltar(await lerErro(resposta), "renomear=" + id));
  }

  revalidatePath("/categorias");
  revalidatePath("/transacoes");
  redirect("/categorias");
}

export async function mesclarCategoria(dados: FormData) {
  const id = Number(lerTexto(dados, "id"));
  const destino = Number(lerTexto(dados, "destino"));

  const resposta = await enviarApi("/categories/" + id + "/merge", "POST", {
    target_id: destino,
  });
  if (!resposta.ok) {
    redirect(paraOndeVoltar(await lerErro(resposta), "mesclar=" + id));
  }

  revalidatePath("/categorias");
  revalidatePath("/transacoes");
  redirect("/categorias");
}

export async function apagarCategoria(dados: FormData) {
  const id = Number(lerTexto(dados, "id"));

  const resposta = await enviarApi("/categories/" + id, "DELETE");
  if (!resposta.ok) {
    redirect(paraOndeVoltar(await lerErro(resposta)));
  }

  revalidatePath("/categorias");
  redirect("/categorias");
}
