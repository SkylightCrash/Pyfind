const form = document.querySelector("#search-form");
const input = document.querySelector("#query");
const section = document.querySelector("#results-section");
const results = document.querySelector("#results");
const title = document.querySelector("#results-title");
const count = document.querySelector("#result-count");
const suggestions = document.querySelector("#suggestions");

function echapper(texte) {
  return String(texte).replace(/[&<>"']/g, caractere => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[caractere]);
}

function mettreEnValeur(texte, requete) {
  let sortie = echapper(texte);
  const mots = requete.replace(/["']/g, "").split(/\s+/)
    .filter(mot => !["ET", "OU", "SAUF"].includes(mot.toUpperCase()));
  mots.forEach(mot => {
    const propre = mot.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    if (propre.length < 2) return;
    const expression = new RegExp(`(${propre.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
    sortie = sortie.replace(expression, "<mark>$1</mark>");
  });
  return sortie;
}

async function rechercher(requete) {
  if (!requete.trim()) return;
  section.hidden = false;
  section.scrollIntoView({ behavior: "smooth", block: "start" });
  title.textContent = requete;
  count.textContent = "Recherche…";
  results.innerHTML = '<div class="empty">Exploration de la bibliothèque…</div>';
  suggestions.innerHTML = "";
  try {
    const reponse = await fetch(`/api/search?q=${encodeURIComponent(requete)}`);
    if (!reponse.ok) throw new Error("Réponse du serveur invalide");
    const donnees = await reponse.json();
    count.textContent = `${donnees.resultats.length} résultat${donnees.resultats.length > 1 ? "s" : ""}`;
    if (donnees.suggestions.length) {
      suggestions.innerHTML = `Aucun mot exact ? Suggestions : ${donnees.suggestions.map(mot =>
        `<button type="button" data-suggestion="${echapper(mot)}">${echapper(mot)}</button>`).join(" · ")}`;
    }
    if (!donnees.resultats.length) {
      results.innerHTML = '<div class="empty">Aucune fable trouvée. Essayez un autre mot ou une autre combinaison.</div>';
      return;
    }
    results.innerHTML = donnees.resultats.map((fable, index) => `
      <article class="result-card" data-fable="${fable.id}" tabindex="0" role="button">
        <div class="result-meta"><span>FABLE N° ${String(fable.id).padStart(3, "0")}</span>
          <span class="score">SCORE ${Number(fable.score).toFixed(5)}</span></div>
        <h3>${echapper(fable.titre)}</h3>
        <p>${mettreEnValeur(fable.extrait, requete)}</p>
        <span class="read-more">Lire la fable →</span>
      </article>`).join("");
  } catch (erreur) {
    count.textContent = "Erreur";
    results.innerHTML = `<div class="empty">${echapper(erreur.message)}. Vérifiez que le serveur Python est lancé.</div>`;
  }
}

form.addEventListener("submit", evenement => {
  evenement.preventDefault();
  rechercher(input.value);
});
document.querySelectorAll(".example").forEach(bouton => {
  bouton.addEventListener("click", () => {
    input.value = bouton.dataset.query;
    rechercher(input.value);
  });
});
suggestions.addEventListener("click", evenement => {
  const bouton = evenement.target.closest("[data-suggestion]");
  if (!bouton) return;
  input.value = bouton.dataset.suggestion;
  rechercher(input.value);
});

async function chargerStats() {
  try {
    const reponse = await fetch("/api/stats");
    const stats = await reponse.json();
    document.querySelector("#stat-fables").textContent = stats.nb_fables.toLocaleString("fr-FR");
    document.querySelector("#stat-words").textContent = stats.nb_mots.toLocaleString("fr-FR");
    document.querySelector("#top-words").innerHTML = stats.top_mots.map(item =>
      `<span>${echapper(item.mot)} <b>${item.frequence}</b></span>`).join("");
  } catch {
    document.querySelector("#top-words").textContent = "Statistiques indisponibles";
  }
}
chargerStats();

/* ---------- Parcourir les fables ---------- */
const listeFables = document.querySelector("#browse-list");
const filtre = document.querySelector("#browse-filter");
const compteurListe = document.querySelector("#browse-count");
const lecteur = document.querySelector("#reader");
const lecteurNum = document.querySelector("#reader-num");
const lecteurTitre = document.querySelector("#reader-title");
const lecteurTexte = document.querySelector("#reader-text");
const boutonPrec = document.querySelector("#reader-prev");
const boutonSuiv = document.querySelector("#reader-next");
let toutesLesFables = [];
let fableOuverte = null;

function simplifier(texte) {
  return texte.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function afficherListe() {
  const terme = simplifier(filtre.value.trim());
  const visibles = toutesLesFables.filter(f => simplifier(f.titre).includes(terme));
  compteurListe.textContent = `${visibles.length} / ${toutesLesFables.length} fables`;
  listeFables.innerHTML = visibles.length ? visibles.map(f => `
    <button type="button" class="browse-item" data-fable="${f.id}">
      <span>${String(f.id).padStart(3, "0")}</span>${echapper(f.titre)}
    </button>`).join("") : '<div class="empty">Aucune fable ne correspond à ce titre.</div>';
}

async function chargerListeFables() {
  try {
    const reponse = await fetch("/api/fables");
    if (!reponse.ok) throw new Error("Réponse du serveur invalide");
    toutesLesFables = await reponse.json();
    afficherListe();
  } catch (erreur) {
    listeFables.innerHTML = `<div class="empty">${echapper(erreur.message)}. Vérifiez que le serveur Python est lancé.</div>`;
  }
}

async function ouvrirFable(id) {
  try {
    const reponse = await fetch(`/api/fable/${id}`);
    if (!reponse.ok) throw new Error("Fable introuvable");
    const fable = await reponse.json();
    fableOuverte = fable.id;
    const position = toutesLesFables.findIndex(f => f.id === fable.id);
    lecteurNum.textContent = `FABLE N° ${String(fable.id).padStart(3, "0")}`;
    lecteurTitre.textContent = fable.titre;
    lecteurTexte.textContent = fable.texte;
    boutonPrec.disabled = position <= 0;
    boutonSuiv.disabled = position < 0 || position >= toutesLesFables.length - 1;
    lecteur.hidden = false;
    lecteur.scrollTop = 0;
    lecteur.querySelector(".reader-panel").scrollTop = 0;
    document.body.style.overflow = "hidden";
  } catch (erreur) {
    alert(erreur.message);
  }
}

function fermerLecteur() {
  lecteur.hidden = true;
  fableOuverte = null;
  document.body.style.overflow = "";
}

function fableVoisine(decalage) {
  const position = toutesLesFables.findIndex(f => f.id === fableOuverte);
  const voisine = toutesLesFables[position + decalage];
  if (voisine) ouvrirFable(voisine.id);
}

document.addEventListener("click", evenement => {
  const cible = evenement.target.closest("[data-fable]");
  if (cible) ouvrirFable(Number(cible.dataset.fable));
});
document.addEventListener("keydown", evenement => {
  const carte = evenement.target.closest?.(".result-card[data-fable]");
  if (carte && (evenement.key === "Enter" || evenement.key === " ")) {
    evenement.preventDefault();
    ouvrirFable(Number(carte.dataset.fable));
    return;
  }
  if (lecteur.hidden) return;
  if (evenement.key === "Escape") fermerLecteur();
  if (evenement.key === "ArrowLeft") fableVoisine(-1);
  if (evenement.key === "ArrowRight") fableVoisine(1);
});
lecteur.addEventListener("click", evenement => { if (evenement.target === lecteur) fermerLecteur(); });
document.querySelector("#reader-close").addEventListener("click", fermerLecteur);
boutonPrec.addEventListener("click", () => fableVoisine(-1));
boutonSuiv.addEventListener("click", () => fableVoisine(1));
filtre.addEventListener("input", afficherListe);
chargerListeFables();
