const overlay = document.getElementById("contactos");
const botoesAbrir = document.querySelectorAll("[data-abrir]");
const botaoFechar = document.querySelector("[data-fechar]");

function abrir() {
  overlay.hidden = false;
  document.body.style.overflow = "hidden";
  window.requestAnimationFrame(function () {
    overlay.classList.add("aberta");
  });
}

function fechar() {
  overlay.classList.remove("aberta");
  document.body.style.overflow = "";
  window.setTimeout(function () {
    if (!overlay.classList.contains("aberta")) {
      overlay.hidden = true;
    }
  }, 320);
}

botoesAbrir.forEach(function (botao) {
  botao.addEventListener("click", abrir);
});

botaoFechar.addEventListener("click", fechar);

overlay.addEventListener("click", function (evento) {
  if (evento.target === overlay) {
    fechar();
  }
});

document.addEventListener("keydown", function (evento) {
  if (evento.key === "Escape") {
    fechar();
  }
});

const observador = new IntersectionObserver(function (entradas) {
  entradas.forEach(function (entrada) {
    if (entrada.isIntersecting) {
      entrada.target.classList.add("visivel");
      observador.unobserve(entrada.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll(".revelar").forEach(function (elemento) {
  observador.observe(elemento);
});

const comparacao = document.querySelector(".comparacao");

const observadorComparacao = new IntersectionObserver(function (entradas) {
  entradas.forEach(function (entrada) {
    if (entrada.isIntersecting) {
      entrada.target.classList.add("riscar");
      observadorComparacao.unobserve(entrada.target);
    }
  });
}, { threshold: 0.6 });

if (comparacao !== null) {
  observadorComparacao.observe(comparacao);
}

const palco = document.querySelector(".palco");

function atualizarPalco() {
  if (palco === null) {
    return;
  }

  const caixa = palco.getBoundingClientRect();
  const altura = window.innerHeight;
  let progresso = (altura - caixa.top) / (altura * 0.75);

  if (progresso < 0) {
    progresso = 0;
  }
  if (progresso > 1) {
    progresso = 1;
  }

  palco.style.setProperty("--p", progresso.toFixed(3));
}

let aEsperar = false;

window.addEventListener("scroll", function () {
  if (aEsperar) {
    return;
  }

  aEsperar = true;
  window.requestAnimationFrame(function () {
    atualizarPalco();
    atualizarHero();
    atualizarNav();
    aEsperar = false;
  });
});

window.addEventListener("resize", atualizarPalco);
atualizarPalco();

const hero = document.querySelector(".hero");

function atualizarHero() {
  if (hero === null) {
    return;
  }

  let progresso = window.scrollY / hero.offsetHeight;

  if (progresso < 0) {
    progresso = 0;
  }
  if (progresso > 1) {
    progresso = 1;
  }

  document.body.style.setProperty("--h", progresso.toFixed(3));
}

window.addEventListener("resize", atualizarHero);
atualizarHero();

const nav = document.querySelector(".nav");
let ultimoY = window.scrollY;

function atualizarNav() {
  const y = window.scrollY;

  if (y > ultimoY && y > 150) {
    nav.classList.add("escondida");
  }
  if (y < ultimoY) {
    nav.classList.remove("escondida");
  }

  ultimoY = y;
}

const ligacaoEmail = document.getElementById("email");

if (ligacaoEmail !== null) {
  const endereco = ligacaoEmail.dataset.nome + String.fromCharCode(64) + ligacaoEmail.dataset.dominio;
  ligacaoEmail.href = "mailto:" + endereco;
  ligacaoEmail.querySelector("span").textContent = endereco;
}

const exemplos = [
  {
    texto: "hoje gastei 30 euros na fnac",
    titulo: "Despesa guardada",
    campos: [
      { nome: "Valor", valor: "30,00 €", palavra: "30 euros", cor: "teal" },
      { nome: "Sítio", valor: "Fnac", palavra: "fnac", cor: "azul" },
      { nome: "Categoria", valor: "Tecnologia", palavra: "", cor: "" },
      { nome: "Data", valor: "Hoje", palavra: "hoje", cor: "berry" }
    ],
    resposta: "Anotado! 30€ na Fnac, categoria Tecnologia.",
    correcao: {
      texto: "afinal foi no continente",
      titulo: "Despesa corrigida",
      campos: [
        { nome: "Sítio", valor: "Continente", palavra: "continente", cor: "azul" },
        { nome: "Categoria", valor: "Alimentação", palavra: "", cor: "" }
      ],
      resposta: "Ah, faz sentido, corrigido: Continente (Alimentação), 30€."
    }
  },
  {
    texto: "ontem 12,50 no uber",
    titulo: "Despesa guardada",
    campos: [
      { nome: "Valor", valor: "12,50 €", palavra: "12,50", cor: "teal" },
      { nome: "Sítio", valor: "Uber", palavra: "uber", cor: "azul" },
      { nome: "Categoria", valor: "Transporte", palavra: "", cor: "" },
      { nome: "Data", valor: "Ontem", palavra: "ontem", cor: "berry" }
    ],
    resposta: "Tá guardado! Uber, 12,50€ em Transporte.",
    correcao: null
  },
  {
    texto: "recebi o salário, 1200",
    titulo: "Entrada guardada",
    campos: [
      { nome: "Valor", valor: "+ 1200,00 €", palavra: "1200", cor: "teal" },
      { nome: "Categoria", valor: "Salário", palavra: "salário", cor: "azul" },
      { nome: "Data", valor: "Hoje", palavra: "", cor: "" }
    ],
    resposta: "Boa, 1200€ de Salário já guardados 👍",
    correcao: null
  }
];

const demoPalco = document.getElementById("demo-palco");
const conversa = document.getElementById("conversa");
const caixaEscrever = document.getElementById("escrever");
const textoEscrito = document.getElementById("escrever-texto");
const ficha = document.getElementById("ficha");
const fichaTitulo = document.getElementById("ficha-titulo");
const fichaLinhas = document.getElementById("ficha-linhas");

let linhas = {};

function esperar(tempo) {
  return new Promise(function (resolver) {
    window.setTimeout(resolver, tempo);
  });
}

async function escrever(texto) {
  caixaEscrever.classList.add("ativo");
  await esperar(400);

  for (let i = 0; i < texto.length; i++) {
    textoEscrito.textContent = textoEscrito.textContent + texto[i];
    await esperar(55);
  }

  caixaEscrever.classList.add("pronto");
  await esperar(450);
  caixaEscrever.classList.add("a-enviar");
  await esperar(150);

  textoEscrito.textContent = "";
  caixaEscrever.classList.remove("ativo");
  caixaEscrever.classList.remove("pronto");
  caixaEscrever.classList.remove("a-enviar");
}

function adicionarBolhaMinha(texto, campos) {
  let html = texto;

  campos.forEach(function (campo) {
    if (campo.palavra !== "") {
      html = html.replace(
        campo.palavra,
        '<span class="marca" data-nome="' + campo.nome + '">' + campo.palavra + "</span>"
      );
    }
  });

  const bolha = document.createElement("div");
  bolha.className = "bolha bolha-eu nova";
  bolha.innerHTML = html;
  conversa.appendChild(bolha);
  return bolha;
}

function adicionarPontos() {
  const bolha = document.createElement("div");
  bolha.className = "bolha bolha-bot pontos nova";
  bolha.innerHTML = "<span></span><span></span><span></span>";
  conversa.appendChild(bolha);
  return bolha;
}

function adicionarBolhaDoBot(texto) {
  const bolha = document.createElement("div");
  bolha.className = "bolha bolha-bot nova";
  bolha.textContent = texto;
  conversa.appendChild(bolha);
}

function criarLinhas(campos) {
  fichaLinhas.innerHTML = "";
  linhas = {};

  campos.forEach(function (campo) {
    const linha = document.createElement("div");
    linha.className = "linha";

    const nome = document.createElement("span");
    nome.textContent = campo.nome;

    const valor = document.createElement("strong");

    linha.appendChild(nome);
    linha.appendChild(valor);
    fichaLinhas.appendChild(linha);
    linhas[campo.nome] = linha;
  });
}

async function voar(marca, alvo, cor) {
  marca.style.setProperty("--cor", "var(--" + cor + ")");
  marca.classList.add("acesa");
  await esperar(400);

  const caixaPalco = demoPalco.getBoundingClientRect();
  const escala = caixaPalco.width / demoPalco.offsetWidth;
  const origem = marca.getBoundingClientRect();
  const destino = alvo.getBoundingClientRect();

  const voo = document.createElement("span");
  voo.className = "voo";
  voo.textContent = marca.textContent;
  voo.style.setProperty("--cor", "var(--" + cor + ")");
  voo.style.fontSize = origem.height / 1.4 / escala + "px";
  voo.style.left = (origem.left - caixaPalco.left) / escala + "px";
  voo.style.top = (origem.top - caixaPalco.top) / escala + "px";
  demoPalco.appendChild(voo);

  const inicio = voo.getBoundingClientRect();
  const tamanho = (destino.height * 1.15) / inicio.height;

  const dx = (destino.right - inicio.right) / escala;
  const dy = (destino.top + destino.height / 2 - (inicio.top + inicio.height / 2)) / escala;
  voo.style.transform = "translate(" + dx + "px, " + dy + "px) scale(" + tamanho + ")";
  voo.style.opacity = "0";

  await esperar(750);
  voo.remove();
}

async function preencher(bolha, campo) {
  const linha = linhas[campo.nome];
  const valor = linha.querySelector("strong");

  if (campo.palavra !== "") {
    const marca = bolha.querySelector('[data-nome="' + campo.nome + '"]');
    await voar(marca, valor, campo.cor);
  } else {
    await esperar(300);
  }

  if (campo.cor !== "") {
    linha.style.setProperty("--cor", "var(--" + campo.cor + ")");
  } else {
    linha.style.setProperty("--cor", "var(--preto)");
  }

  valor.classList.remove("cheio");
  valor.getBoundingClientRect();
  valor.textContent = campo.valor;
  valor.classList.add("cheio");
  linha.classList.add("acesa");

  await esperar(350);
  linha.classList.remove("acesa");
}

async function conversar(texto, campos, titulo, resposta) {
  await escrever(texto);
  const bolha = adicionarBolhaMinha(texto, campos);
  await esperar(500);

  const pontos = adicionarPontos();
  fichaTitulo.textContent = "A ler a mensagem";
  ficha.classList.add("mostrar");
  await esperar(500);

  for (let i = 0; i < campos.length; i++) {
    await preencher(bolha, campos[i]);
  }

  await esperar(300);
  fichaTitulo.textContent = titulo;
  pontos.remove();
  adicionarBolhaDoBot(resposta);
}

async function mostrarExemplo(exemplo) {
  conversa.classList.add("a-limpar");
  ficha.classList.remove("mostrar");
  await esperar(450);

  conversa.innerHTML = "";
  conversa.classList.remove("a-limpar");
  criarLinhas(exemplo.campos);
  await esperar(300);

  await conversar(exemplo.texto, exemplo.campos, exemplo.titulo, exemplo.resposta);

  if (exemplo.correcao !== null) {
    await esperar(1800);
    const correcao = exemplo.correcao;
    await conversar(correcao.texto, correcao.campos, correcao.titulo, correcao.resposta);
  }

  await esperar(3500);
}

async function comecarDemo() {
  let indice = 0;

  while (true) {
    await mostrarExemplo(exemplos[indice]);
    indice = indice + 1;
    if (indice >= exemplos.length) {
      indice = 0;
    }
  }
}

function ajustarEscala() {
  if (demoPalco === null) {
    return;
  }

  demoPalco.style.setProperty("--escala", demoPalco.offsetWidth / 996);
}

window.addEventListener("resize", ajustarEscala);
ajustarEscala();

const reduzirMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (demoPalco !== null && !reduzirMovimento) {
  comecarDemo();
}
