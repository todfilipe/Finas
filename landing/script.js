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
