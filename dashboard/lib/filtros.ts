export type Filtros = {
  texto: string;
  tipo: string;
  categoria: string;
  comerciante: string;
  de: string;
  ate: string;
  min: string;
  max: string;
};

function ler(parametros: Record<string, string | string[] | undefined>, nome: string) {
  const valor = parametros[nome];
  return typeof valor === "string" ? valor.trim() : "";
}

function dataValida(texto: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(texto);
}

function valorValido(texto: string) {
  const numero = Number(texto);
  return texto !== "" && Number.isFinite(numero) && numero >= 0;
}

export function lerFiltros(parametros: Record<string, string | string[] | undefined>): Filtros {
  const de = ler(parametros, "de");
  const ate = ler(parametros, "ate");
  const min = ler(parametros, "min");
  const max = ler(parametros, "max");

  const tipo = ler(parametros, "tipo");

  return {
    texto: ler(parametros, "texto"),
    tipo: tipo === "despesa" || tipo === "receita" ? tipo : "",
    categoria: ler(parametros, "categoria"),
    comerciante: ler(parametros, "comerciante"),
    de: dataValida(de) ? de : "",
    ate: dataValida(ate) ? ate : "",
    min: valorValido(min) ? min : "",
    max: valorValido(max) ? max : "",
  };
}

export function lerPagina(parametros: Record<string, string | string[] | undefined>) {
  const numero = Number(ler(parametros, "pagina"));
  if (!Number.isFinite(numero) || numero < 1) {
    return 1;
  }

  return Math.floor(numero);
}

export function consultaDaApi(filtros: Filtros, limite: number, pagina: number) {
  const consulta = new URLSearchParams();

  if (filtros.texto) {
    consulta.set("search", filtros.texto);
  }
  if (filtros.tipo) {
    consulta.set("kind", filtros.tipo === "receita" ? "income" : "expense");
  }
  if (filtros.categoria) {
    consulta.set("category", filtros.categoria);
  }
  if (filtros.comerciante) {
    consulta.set("merchant", filtros.comerciante);
  }
  if (filtros.de) {
    consulta.set("start_date", filtros.de);
  }
  if (filtros.ate) {
    consulta.set("end_date", filtros.ate);
  }
  if (filtros.min) {
    consulta.set("min_cents", String(Math.round(Number(filtros.min) * 100)));
  }
  if (filtros.max) {
    consulta.set("max_cents", String(Math.round(Number(filtros.max) * 100)));
  }

  consulta.set("limit", String(limite));
  consulta.set("offset", String((pagina - 1) * limite));

  return consulta.toString();
}

export function linkDaPagina(filtros: Filtros, pagina: number) {
  const parametros = new URLSearchParams();

  if (filtros.texto) {
    parametros.set("texto", filtros.texto);
  }
  if (filtros.tipo) {
    parametros.set("tipo", filtros.tipo);
  }
  if (filtros.categoria) {
    parametros.set("categoria", filtros.categoria);
  }
  if (filtros.comerciante) {
    parametros.set("comerciante", filtros.comerciante);
  }
  if (filtros.de) {
    parametros.set("de", filtros.de);
  }
  if (filtros.ate) {
    parametros.set("ate", filtros.ate);
  }
  if (filtros.min) {
    parametros.set("min", filtros.min);
  }
  if (filtros.max) {
    parametros.set("max", filtros.max);
  }
  if (pagina > 1) {
    parametros.set("pagina", String(pagina));
  }

  const consulta = parametros.toString();
  return consulta ? "/transacoes?" + consulta : "/transacoes";
}

export function haFiltros(filtros: Filtros) {
  return (
    filtros.texto !== "" ||
    filtros.tipo !== "" ||
    filtros.categoria !== "" ||
    filtros.comerciante !== "" ||
    filtros.de !== "" ||
    filtros.ate !== "" ||
    filtros.min !== "" ||
    filtros.max !== ""
  );
}

export function juntarAoLink(link: string, extra: string) {
  return link + (link.includes("?") ? "&" : "?") + extra;
}

export function linkDaLinha(filtros: Filtros, pagina: number, acao: string, id: number) {
  return juntarAoLink(linkDaPagina(filtros, pagina), acao + "=" + id);
}

export function lerId(parametros: Record<string, string | string[] | undefined>, nome: string) {
  const numero = Number(ler(parametros, nome));
  if (!Number.isFinite(numero) || numero < 1) {
    return 0;
  }

  return Math.floor(numero);
}
