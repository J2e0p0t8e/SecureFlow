(function () {
  var STORAGE_KEY = "secureflow-locale";

  var STRINGS = {
    fr: {
      "nav.home": "Accueil",
      "nav.launch": "Lancer la plateforme",
      "nav.modes": "Produit",
      "nav.band": "Band Room",
      "nav.how": "Fonctionnement",
      "pill.hackathon": "Band of Agents Hackathon 2026",
      "app.title": "SecureFlow AI",
      "app.subtitle": "Analyse de sécurité propulsée par des agents IA",
      "mode.a.title": "Audit-to-Fix",
      "mode.a.desc": "Audit RGPD/OWASP → remédiation supervisée ou rapport PDF",
      "product.deliverables": "Branche CRITIQUE/CORRIGER → patch ZIP · Branche PROPRE/SURVEILLER → rapport PDF",
      "agents.title": "Équipe d'agents",
      "agents.hint": "Recrutement dynamique dans Band — seuls Scanner et Threat démarrent, les autres rejoignent si la situation l'exige.",
      "field.github": "Lien GitHub",
      "field.zip": "Upload ZIP",
      "field.zip.choose": "Choisir un fichier .zip",
      "field.code": "Code source",
      "hint.github": "GitHub, ZIP ou code collé — au moins une source",
      "hint.modeA": "Audit-to-Fix : triage, décision, remédiation ou rapport PDF selon le verdict",
      "hint.modeC": "Mode C : audit formel d'un dépôt complet (GitHub ou ZIP obligatoire, jusqu'à 50 fichiers)",
      "hint.modeB": "Mode B : précisez la stack souhaitée — les agents conçoivent et développent le projet.",
      "field.repo": "Dépôt à auditer",
      "field.repo.placeholder": "Non utilisé en Mode C — fournissez GitHub ou ZIP ci-dessus",
      "field.code.placeholderA": "Collez du code à auditer, ou utilisez GitHub / ZIP ci-dessus",
      "field.code.placeholderB": "Ex : Application todo-list avec auth JWT, API REST…",
      "field.desc": "Description du projet (from scratch)",
      "btn.triage": "Lancer le triage",
      "btn.audit": "Lancer l'audit",
      "btn.dev": "Lancer le pipeline dev",
      "btn.report": "Générer le rapport PDF",
      "session.band": "Band Room",
      "session.back": "Retour",
      "session.connecting": "Connexion à la Band Room…",
      "session.connected": "Band Room connectée — les agents collaborent.",
      "session.band.live": "Fil Band en direct — les agents @mentionnent et recrutent ici.",
      "session.band.open": "Ouvrir dans Band",
      "session.typing": "{agent} écrit",
      "session.handoff": "{from} passe la main à {to}",
      "session.analysis.done": "Analyse terminée.",
      "session.agent.start": "Je démarre mon analyse ({agent}).",
      "session.error.failed": "Analyse échouée",
      "session.mode.tag": "Mode {mode} — {count} agent(s)",
      "human.review.title": "Validation humaine requise",
      "human.review.default": "Décision CRITIQUE/CORRIGER — approuvez la remédiation (patch ZIP) ou annulez.",
      "human.review.band.title": "Répondez dans la Band Room",
      "human.review.band.instructions": "Ouvrez la Room Band et répondez dans le fil avec APPROUVE ou REJETE. SecureFlow reprend automatiquement quand votre message apparaît dans Band.",
      "human.review.band.open": "Ouvrir la Band Room",
      "human.review.shortcut": "Raccourci web (poste aussi dans Band) :",
      "human.review.comment.placeholder": "Commentaire optionnel (enregistré dans la Band Room)…",
      "human.review.proceed": "Raccourci APPROUVE",
      "human.review.abort": "Raccourci REJETE",
      "human.review.sent.proceed": "Validation enregistrée — remédiation via Band Room…",
      "human.review.sent.abort": "Audit annulé — décision enregistrée dans la Band Room.",
      "intro.ScannerAgent": "Je commence la cartographie sécurité du projet.",
      "intro.ThreatAgent": "J'analyse les menaces et vulnérabilités exploitables.",
      "intro.ComplianceAgent": "Je vérifie la conformité réglementaire.",
      "intro.RiskAgent": "J'évalue les risques et leur criticité.",
      "intro.DecisionAgent": "Je prépare la décision finale.",
      "intro.FeasibilityAgent": "J'évalue la faisabilité du projet.",
      "intro.ArchitectAgent": "Je définis l'architecture technique.",
      "intro.DesignAgent": "Je conçois l'expérience utilisateur.",
      "intro.DevAgent": "Je génère le code du projet.",
      "intro.SecurityAgent": "J'audite le code généré.",
      "intro.QAAgent": "Je valide la qualité du livrable.",
      "intro.MetricsAgent": "Je calcule les métriques de sécurité.",
      "intro.ReportAgent": "Je rédige le rapport final.",
      "label.ScannerAgent": "Scanner",
      "label.ThreatAgent": "Threat",
      "label.ComplianceAgent": "Compliance",
      "label.RiskAgent": "Risk",
      "label.DecisionAgent": "Decision",
      "label.FeasibilityAgent": "Faisabilité",
      "label.ArchitectAgent": "Architecte",
      "label.DesignAgent": "Design",
      "label.DevAgent": "Dev",
      "label.SecurityAgent": "Sécurité",
      "label.QAAgent": "QA",
      "label.MetricsAgent": "Métriques",
      "label.ReportAgent": "Rapport",
      "btn.zip.download": "Télécharger le projet ZIP",
      "btn.zip.patch": "Télécharger le patch ZIP",
      "btn.zip.file": "fichier",
      "btn.zip.files": "fichiers",
      "btn.pdf": "Télécharger le rapport PDF",
      "btn.html": "Télécharger le rapport HTML",
      "btn.zip": "Télécharger le projet (ZIP)",
      "hint.modeC.pdf": "Le livrable principal du Mode C est le rapport PDF professionnel.",
      "alert.input": "Veuillez entrer un lien GitHub, du texte ou un fichier ZIP.",
      "alert.modeC": "Mode C : fournissez un lien GitHub ou une archive ZIP (audit formel de dépôt complet).",
      "alert.modeB": "Mode B : décrivez le projet à créer (au moins quelques phrases).",
      "verdict.title": "Verdict Audit-to-Fix",
      "deliverables.both": "Téléchargez le rapport PDF d'audit et le patch ZIP de remédiation.",
      "deliverables.pdf": "Téléchargez le rapport PDF d'audit formel.",
      "verdict.score": "Score de risque",
      "verdict.fix": "Fix now",
      "verdict.id": "ID",
      "coverage": "Couverture",
      "files.analyzed": "fichiers analysés",
      "score.security": "Score sécurité",
      "decision": "Décision",
      "decision.download": "téléchargez le PDF pour le rapport complet",
      "error.prefix": "Erreur",
      "hero.title": "Passez vos audits RGPD/OWASP sans bloquer votre roadmap",
      "hero.lead": "SecureFlow AI aide les équipes SaaS européennes à auditer leur code, trancher en GO/NO-GO, et corriger automatiquement ce qu'il trouve — sous supervision humaine, dans une Band Room où les agents se recrutent et débattent en direct.",
      "hero.cta": "Lancer un audit-to-fix",
      "hero.discover": "Voir la collaboration Band",
      "stat.modes": "pipeline audit-to-fix",
      "stat.agents": "agents Band recrutables",
      "stat.room": "source de vérité LLM",
      "band.label": "Band of Agents",
      "band.title": "Band est le moteur, pas un widget chat",
      "band.desc": "Chaque agent lit l'historique Band avant d'agir. Recrutement conditionnel, escalades, désaccords visibles et validation humaine bloquante — tout est tracé dans la Room.",
      "band.recruit.title": "Recrutement dynamique",
      "band.recruit.desc": "ComplianceAgent ou RiskAgent apparaissent dans la Room quand Threat le justifie — pas une liste figée au démarrage.",
      "band.disagree.title": "Désaccord & arbitrage",
      "band.disagree.desc": "Si Threat et Compliance divergent (≥3 pts), un event DÉSACCORD DÉTECTÉ force DecisionAgent à trancher explicitement.",
      "band.human.title": "Validation humaine",
      "band.human.desc": "Décision CRITIQUE/CORRIGER → pause obligatoire. L'opérateur approuve ou rejette la remédiation avant DevAgent.",
      "project.label": "Le projet",
      "project.title": "Qu'est-ce que SecureFlow AI ?",
      "project.desc": "Réduisez le temps de triage vulnérabilités avant mise en conformité RGPD/OWASP. Un seul flux : scan → menaces → décision → (remédiation ZIP ou rapport PDF). Valeur métier chiffrable : heures gagnées sur le tri manuel + patch proposé à relire.",
      "about.collab.title": "Collaboration multi-agents",
      "about.collab.desc": "La Band Room est la source de vérité : chaque agent lit get_context() avant le LLM. Recrutements, escalades et décisions humaines y sont publiés — sans contourner Band.",
      "about.security.title": "Sécurité by design",
      "about.security.desc": "Verdict GO/NO-GO, score /10, checklist Fix now, patch ZIP ou PDF /100. Remédiation texte-in/texte-out (fichiers corrigés à relire, jamais appliqués automatiquement).",
      "modes.label": "Produit",
      "modes.title": "Audit-to-Fix — un flux, deux livrables",
      "modes.desc": "La phase évolue pendant l'exécution. Branche remédiation (CRITIQUE/CORRIGER) → patch ZIP. Branche propre/surveiller → rapport PDF.",
      "landing.modeA.title": "Audit-to-Fix",
      "landing.modeA.tag": "Un seul produit · GitHub, ZIP ou code",
      "landing.modeA.desc": "scanning → triage → decision → validation humaine si besoin → remédiation (Dev/Security/QA + re-scan → ZIP) ou reporting (Metrics/Report → PDF). Recrutement Compliance/Risk/Decision dynamique dans Band.",
      "landing.deliverables": "* recrutés dynamiquement · ZIP = branche CRITIQUE/CORRIGER · PDF = branche PROPRE/SURVEILLER",
      "chip.feasibility": "Faisabilité",
      "chip.architect": "Architecte",
      "chip.design": "Design",
      "chip.security": "Sécurité",
      "chip.metrics": "Métriques",
      "chip.report": "Rapport",
      "how.label": "Fonctionnement",
      "how.title": "Comment ça marche ?",
      "how.desc": "Ouvrez votre démo sur la Band Room : c'est là que le jury voit recrutements, désaccords et validation humaine.",
      "step1.title": "Importer le dépôt",
      "step1.desc": "GitHub, ZIP ou extrait de code — Scanner seed la Room Band.",
      "step2.title": "Observer la Room",
      "step2.desc": "Agents recrutés à la volée, escalades, désaccords, @mentions.",
      "step3.title": "Valider si CRITIQUE",
      "step3.desc": "Approuver la remédiation ou annuler — décision publiée dans Band.",
      "step4.title": "Récupérer le livrable",
      "step4.desc": "Patch ZIP (remédiation) ou PDF formel (projet propre) + verdict /10.",
      "stack.label": "Stack & partenaires",
      "stack.title": "Technologie & prix hackathon",
      "stack.desc": "Band AI coordonne ; Featherless par défaut (modèles open-source) ; AI/ML API pour MetricsAgent.",
      "stack.note": "<strong>Partenaires hackathon.</strong> DevAgent (remédiation) s'appuie sur Featherless (modèles open-source) ; MetricsAgent peut utiliser AI/ML API si les clés sont configurées.",
      "cta.title": "Prêt pour votre démo Band ?",
      "cta.desc": "Lancez un audit-to-fix et ouvrez la Band Room en premier plan.",
      "cta.btn": "Accéder à la plateforme",
      "footer.project": "SecureFlow AI — Projet hackathon Band of Agents 2026",
      "footer.tagline": "Auditer · Corriger · Conformité RGPD/OWASP",
    },
    en: {
      "nav.home": "Home",
      "nav.launch": "Open platform",
      "nav.modes": "Product",
      "nav.band": "Band Room",
      "nav.how": "How it works",
      "pill.hackathon": "Band of Agents Hackathon 2026",
      "app.title": "SecureFlow AI",
      "app.subtitle": "Security analysis powered by AI agents",
      "mode.a.title": "Audit-to-Fix",
      "mode.a.desc": "GDPR/OWASP audit → supervised remediation or PDF report",
      "product.deliverables": "CRITIQUE/CORRIGER branch → patch ZIP · CLEAN/WATCH branch → PDF report",
      "agents.title": "Agent team",
      "agents.hint": "Dynamic Band recruitment — only Scanner and Threat start; others join when needed.",
      "hint.github": "GitHub, ZIP or pasted code — at least one source required",
      "hint.modeA": "Audit-to-Fix: triage, decision, remediation or PDF report depending on verdict",
      "hint.modeC": "Mode C: formal audit of a full repo (GitHub or ZIP required, up to 50 files)",
      "hint.modeB": "Mode B: specify your desired stack — agents design and build the project.",
      "field.repo": "Repository to audit",
      "field.repo.placeholder": "Not used in Mode C — provide GitHub or ZIP above",
      "field.code.placeholderA": "Paste code to audit, or use GitHub / ZIP above",
      "field.code.placeholderB": "E.g. Todo app with JWT auth, REST API, React UI…",
      "field.desc": "Project description (from scratch)",
      "btn.triage": "Start triage",
      "btn.audit": "Start audit",
      "btn.dev": "Start dev pipeline",
      "btn.report": "Generate PDF report",
      "session.band": "Band Room",
      "session.back": "Back",
      "session.connecting": "Connecting to Band Room…",
      "session.connected": "Band Room connected — agents are collaborating.",
      "session.band.live": "Live Band thread — agents @mention and recruit here.",
      "session.band.open": "Open in Band",
      "session.typing": "{agent} is typing",
      "session.handoff": "{from} hands off to {to}",
      "session.analysis.done": "Analysis complete.",
      "session.agent.start": "Starting my analysis ({agent}).",
      "session.error.failed": "Analysis failed",
      "session.mode.tag": "Mode {mode} — {count} agent(s)",
      "human.review.title": "Human validation required",
      "human.review.default": "CRITIQUE/CORRIGER decision — approve remediation (patch ZIP) or abort.",
      "human.review.band.title": "Reply in the Band Room",
      "human.review.band.instructions": "Open the Band Room and reply in the thread with APPROVE or REJECT. SecureFlow resumes automatically when your message appears in Band.",
      "human.review.band.open": "Open Band Room",
      "human.review.shortcut": "Web shortcut (also posts to Band):",
      "human.review.comment.placeholder": "Optional comment (recorded in the Band Room)…",
      "human.review.proceed": "Shortcut APPROVE",
      "human.review.abort": "Shortcut REJECT",
      "human.review.sent.proceed": "Validation recorded — remediation resumes via Band Room…",
      "human.review.sent.abort": "Audit aborted — decision recorded in the Band Room.",
      "intro.ScannerAgent": "Starting the project security mapping.",
      "intro.ThreatAgent": "Analyzing exploitable threats and vulnerabilities.",
      "intro.ComplianceAgent": "Checking regulatory compliance.",
      "intro.RiskAgent": "Assessing risks and their severity.",
      "intro.DecisionAgent": "Preparing the final decision.",
      "intro.FeasibilityAgent": "Assessing project feasibility.",
      "intro.ArchitectAgent": "Defining the technical architecture.",
      "intro.DesignAgent": "Designing the user experience.",
      "intro.DevAgent": "Generating the project code.",
      "intro.SecurityAgent": "Auditing the generated code.",
      "intro.QAAgent": "Validating deliverable quality.",
      "intro.MetricsAgent": "Computing security metrics.",
      "intro.ReportAgent": "Writing the final report.",
      "label.ScannerAgent": "Scanner",
      "label.ThreatAgent": "Threat",
      "label.ComplianceAgent": "Compliance",
      "label.RiskAgent": "Risk",
      "label.DecisionAgent": "Decision",
      "label.FeasibilityAgent": "Feasibility",
      "label.ArchitectAgent": "Architect",
      "label.DesignAgent": "Design",
      "label.DevAgent": "Dev",
      "label.SecurityAgent": "Security",
      "label.QAAgent": "QA",
      "label.MetricsAgent": "Metrics",
      "label.ReportAgent": "Report",
      "btn.zip.download": "Download project ZIP",
      "btn.zip.file": "file",
      "btn.zip.files": "files",
      "btn.pdf": "Download PDF report",
      "btn.html": "Download HTML report",
      "btn.zip": "Download project (ZIP)",
      "hint.modeC.pdf": "Mode C's main deliverable is the professional PDF report.",
      "alert.input": "Please enter a GitHub link, text, or ZIP file.",
      "alert.modeC": "Mode C: provide a GitHub link or ZIP archive (formal full-repo audit).",
      "alert.modeB": "Mode B: describe the project to build (at least a few sentences).",
      "verdict.title": "Audit-to-Fix verdict",
      "deliverables.both": "Download the audit PDF and the remediation patch ZIP.",
      "deliverables.pdf": "Download the formal audit PDF.",
      "verdict.score": "Risk score",
      "verdict.fix": "Fix now",
      "verdict.id": "ID",
      "coverage": "Coverage",
      "files.analyzed": "files analyzed",
      "score.security": "Security score",
      "decision": "Decision",
      "decision.download": "download the PDF for the full report",
      "error.prefix": "Error",
      "hero.title": "Pass GDPR/OWASP audits without blocking your roadmap",
      "hero.lead": "SecureFlow AI helps European SaaS teams audit code, decide GO/NO-GO, and automatically fix findings — under human supervision, in a Band Room where agents recruit and debate in real time.",
      "hero.cta": "Start audit-to-fix",
      "hero.discover": "See Band collaboration",
      "stat.modes": "audit-to-fix pipeline",
      "stat.agents": "recruitable Band agents",
      "stat.room": "LLM source of truth",
      "band.label": "Band of Agents",
      "band.title": "Band is the engine, not a chat widget",
      "band.desc": "Every agent reads Band history before acting. Conditional recruitment, escalations, visible disagreements, and blocking human validation — all traced in the Room.",
      "band.recruit.title": "Dynamic recruitment",
      "band.recruit.desc": "ComplianceAgent or RiskAgent appear in the Room when Threat requires it — not a fixed list at startup.",
      "band.disagree.title": "Disagreement & arbitration",
      "band.disagree.desc": "If Threat and Compliance diverge (≥3 pts), a DISAGREEMENT DETECTED event forces DecisionAgent to rule explicitly.",
      "band.human.title": "Human validation",
      "band.human.desc": "CRITIQUE/CORRIGER decision → mandatory pause. Operator approves or rejects remediation before DevAgent.",
      "project.label": "The project",
      "project.title": "What is SecureFlow AI?",
      "project.desc": "Reduce time spent triaging vulnerabilities before GDPR/OWASP compliance. One flow: scan → threats → decision → (remediation ZIP or PDF report). Measurable value: hours saved on manual triage + patch to review.",
      "about.collab.title": "Multi-agent collaboration",
      "about.collab.desc": "The Band Room is the source of truth: every agent calls get_context() before the LLM. Recruitments, escalations, and human decisions are published there — without bypassing Band.",
      "about.security.title": "Security by design",
      "about.security.desc": "GO/NO-GO verdict, /10 score, Fix now checklist, patch ZIP or /100 PDF. Text-in/text-out remediation (corrected files to review, never auto-applied).",
      "modes.label": "Product",
      "modes.title": "Audit-to-Fix — one flow, two deliverables",
      "modes.desc": "Phase evolves during execution. Remediation branch (CRITIQUE/CORRIGER) → patch ZIP. Clean/watch branch → PDF report.",
      "landing.modeA.title": "Audit-to-Fix",
      "landing.modeA.tag": "Single product · GitHub, ZIP or code",
      "landing.modeA.desc": "scanning → triage → decision → human validation if needed → remediation (Dev/Security/QA + re-scan → ZIP) or reporting (Metrics/Report → PDF). Dynamic Compliance/Risk/Decision recruitment in Band.",
      "landing.deliverables": "* dynamically recruited · ZIP = CRITIQUE/CORRIGER branch · PDF = CLEAN/WATCH branch",
      "chip.feasibility": "Feasibility",
      "chip.architect": "Architect",
      "chip.design": "Design",
      "chip.security": "Security",
      "chip.metrics": "Metrics",
      "chip.report": "Report",
      "how.label": "How it works",
      "how.title": "How does it work?",
      "how.desc": "Open your demo on the Band Room — that's where judges see recruitment, disagreements, and human validation.",
      "step1.title": "Import the repo",
      "step1.desc": "GitHub, ZIP or code paste — Scanner seeds the Band Room.",
      "step2.title": "Watch the Room",
      "step2.desc": "Agents recruited on the fly, escalations, disagreements, @mentions.",
      "step3.title": "Validate if CRITIQUE",
      "step3.desc": "Approve remediation or abort — decision published in Band.",
      "step4.title": "Get the deliverable",
      "step4.desc": "Patch ZIP (remediation) or formal PDF (clean project) + /10 verdict.",
      "stack.label": "Stack & partners",
      "stack.title": "Technology & hackathon prizes",
      "stack.desc": "Band AI coordinates; Featherless by default (open-source models); AI/ML API for MetricsAgent.",
      "stack.note": "<strong>Hackathon partners.</strong> DevAgent (remediation) runs on Featherless (open-source models); MetricsAgent can use AI/ML API when keys are configured.",
      "cta.title": "Ready for your Band demo?",
      "cta.desc": "Launch an audit-to-fix and put the Band Room front and center.",
      "cta.btn": "Open the platform",
      "footer.project": "SecureFlow AI — Band of Agents 2026 hackathon project",
      "footer.tagline": "Audit · Fix · GDPR/OWASP compliance",
    },
  };

  function normalize(value) {
    return value === "en" ? "en" : "fr";
  }

  function preferredLocale() {
    var saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "fr") return saved;
    return (navigator.language || "").toLowerCase().startsWith("en") ? "en" : "fr";
  }

  function t(key, vars) {
    var locale = normalize(preferredLocale());
    var val = (STRINGS[locale] && STRINGS[locale][key]) || STRINGS.fr[key] || key;
    if (vars) {
      Object.keys(vars).forEach(function (k) {
        val = val.replace(new RegExp("\\{" + k + "\\}", "g"), String(vars[k]));
      });
    }
    return val;
  }

  function applyTranslations(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var val = t(key);
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        if (el.hasAttribute("data-i18n-placeholder")) el.placeholder = val;
        else el.value = val;
      } else {
        el.textContent = val;
      }
    });
    scope.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
    });
    scope.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      el.innerHTML = t(el.getAttribute("data-i18n-html"));
    });
    document.querySelectorAll("[data-lang-toggle]").forEach(function (btn) {
      var locale = normalize(preferredLocale());
      var label = btn.querySelector("[data-lang-label]");
      if (label) label.textContent = locale === "en" ? "EN" : "FR";
      btn.setAttribute(
        "aria-label",
        locale === "en" ? "Switch to French" : "Passer en anglais"
      );
      btn.setAttribute("title", locale === "en" ? "Français" : "English");
    });
  }

  function setLocale(locale) {
    var code = normalize(locale);
    localStorage.setItem(STORAGE_KEY, code);
    document.documentElement.lang = code;
    applyTranslations();
    if (typeof window.updateFormForMode === "function") window.updateFormForMode();
    if (typeof window.updateAgentSelector === "function") window.updateAgentSelector();
  }

  window.SecureFlowI18n = {
    get: function () {
      return normalize(preferredLocale());
    },
    set: setLocale,
    toggle: function () {
      setLocale(this.get() === "en" ? "fr" : "en");
    },
    t: t,
    apply: applyTranslations,
  };

  document.addEventListener("DOMContentLoaded", function () {
    setLocale(preferredLocale());
    document.querySelectorAll("[data-lang-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        window.SecureFlowI18n.toggle();
      });
    });
  });
})();
