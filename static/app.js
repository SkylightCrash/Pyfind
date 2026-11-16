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
      <article class="result-card">
        <div class="result-meta"><span>FABLE N° ${String(fable.id).padStart(3, "0")}</span>
          <span class="score">SCORE ${Number(fable.score).toFixed(5)}</span></div>
        <h3>${echapper(fable.titre)}</h3>
        <p>${mettreEnValeur(fable.extrait, requete)}</p>
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
