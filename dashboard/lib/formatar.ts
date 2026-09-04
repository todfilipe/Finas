export function formatarDinheiro(centimos: number, moeda: string) {
  return new Intl.NumberFormat("pt-PT", {
    style: "currency",
    currency: moeda,
  }).format(centimos / 100);
}

export function formatarDinheiroCurto(centimos: number, moeda: string) {
  return new Intl.NumberFormat("pt-PT", {
    style: "currency",
    currency: moeda,
    maximumFractionDigits: 0,
  }).format(centimos / 100);
}

function dataDoMes(mes: string) {
  const partes = mes.split("-");
  return new Date(Number(partes[0]), Number(partes[1]) - 1, 1);
}

export function nomeDoMes(mes: string) {
  return new Intl.DateTimeFormat("pt-PT", { month: "long", year: "numeric" }).format(
    dataDoMes(mes)
  );
}

export function nomeDoMesSemAno(mes: string) {
  return new Intl.DateTimeFormat("pt-PT", { month: "long" }).format(dataDoMes(mes));
}

export function nomeCurtoDoMes(mes: string) {
  const nome = new Intl.DateTimeFormat("pt-PT", { month: "short" }).format(dataDoMes(mes));
  return nome.replace(".", "");
}

export function mesAtual() {
  const hoje = new Date();
  return hoje.getFullYear() + "-" + String(hoje.getMonth() + 1).padStart(2, "0");
}

export function mesAnterior(mes: string) {
  const data = dataDoMes(mes);
  data.setMonth(data.getMonth() - 1);
  return data.getFullYear() + "-" + String(data.getMonth() + 1).padStart(2, "0");
}

export function mesSeguinte(mes: string) {
  const data = dataDoMes(mes);
  data.setMonth(data.getMonth() + 1);
  return data.getFullYear() + "-" + String(data.getMonth() + 1).padStart(2, "0");
}

export function mesValido(mes: string) {
  if (!/^\d{4}-\d{2}$/.test(mes)) {
    return false;
  }

  const numero = Number(mes.split("-")[1]);
  return numero >= 1 && numero <= 12;
}

export function percentagem(valor: number, total: number) {
  if (total <= 0) {
    return 0;
  }
  return Math.round((valor / total) * 100);
}

export function formatarData(dataIso: string) {
  const partes = dataIso.split("-");
  const data = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
  return new Intl.DateTimeFormat("pt-PT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(data);
}
