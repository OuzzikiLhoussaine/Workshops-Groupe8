# Workshop 2 DevSecOps — SAST et SCA sur OWASP Juice Shop (Groupe 8)

## 1. Objectif
Mettre en place une chaîne DevSecOps sur une application volontairement vulnérable (OWASP Juice Shop v20.3.0, licence MIT) : analyse statique de code (SAST), analyse de composition logicielle (SCA), intégration continue (GitHub Actions) et security gate. Ce document est le rapport final du workshop.

## 2. Équipe et rôles
| Personne | Rôle |
|---|---|
| Ouzziki Lhoussaine | Rôle A (Semgrep, SonarQube) + Rôle B (Dependency-Check, Dependabot) + Rôle C (pipeline, security gate, rapport) |
| Zineb Hajaj | Collaboratrice : revue des pull requests |
| Hasna Elhassani | Collaboratrice : revue des pull requests |

Pour ce workshop, les trois rôles ont été tenus par le responsable ; les deux collaboratrices restent relectrices et pourront prendre des rôles au workshop 3.

## 3. Organisation du dépôt et politique de pull requests
- `workshop-2-sast-sca` : branche principale du projet (branche par défaut du dépôt).
- `main` : page d'index uniquement.
- `workshop-2/<nom>-<tâche>` : branches de travail ; toute modification passe par une pull request vers `workshop-2-sast-sca`.
- Protection de branche : pull request requise + 1 approbation. Le responsable dispose d'un contournement d'urgence (administrateur), utilisé uniquement quand aucune relecture n'est possible et tracé ici.
- Règle absolue : jamais de pull request depuis une branche de travail vers `main`.
- Incident du 24/10/2026 : une pull request accidentelle (#7, bouton « Compare & pull request » avec une base erronée) a importé tout le projet dans `main`. Détecté et annulé le jour même par la pull request corrective #12 (git revert). Aucune règle de protection n'a été assouplie pour masquer cet incident.
- Incident du 25/10/2026 : deux pull requests de mise à jour Dependabot (#10, #11) ont été fusionnées par erreur, malgré la politique ci-dessous ; annulées par revert (pull request #13).

## 4. Outils, pipeline et exécution
| Couche | Outil | Exécution |
|---|---|---|
| SAST | Semgrep (pack de règles `p/owasp-top-ten`) | local + CI |
| SAST | SonarQube Community 9.9.8 | local (Docker Compose) |
| SCA | OWASP Dependency-Check | CI (base NVD en cache, clé API NVD via secret) |
| SCA | npm audit, Dependabot | local + GitHub (onglet Security) |
| Gate | `scripts/security_gate.py` | CI (job `security-gate`) |

Pipeline `DevSecOps Pipeline` (`.github/workflows/devsecops-pipeline.yml`) :
1. `build-and-test` : Node 24, `npm ci`, `npm run build` (zéro erreur de compilation).
2. `sast-sca-semgrep` : scan Semgrep, rapports JSON et SARIF (artefact `semgrep-report`).
3. `sca-dependency-check` : OWASP Dependency-Check sur `package-lock.json` et `frontend/package-lock.json` (artefact `dependency-check-report`).
4. `security-gate` : évalue les rapports selon la politique de la section 7 et bloque le build si nécessaire.

Déclencheurs : push sur `workshop-2-sast-sca` et `workshop-2/**`, pull request vers `workshop-2-sast-sca`, exécution manuelle (workflow_dispatch). Toutes les actions GitHub sont épinglées à leurs empreintes SHA complètes (protection de la chaîne d'approvisionnement).

Reproduction locale : Semgrep via `semgrep --config p/owasp-top-ten --json-output=semgrep-results.json --sarif-output=semgrep-results.sarif .` ; Dependency-Check via le conteneur `owasp/dependency-check:latest` ; gate via `python3 scripts/security_gate.py` (rapports dans `reports/semgrep/` et `reports/odc/`).

## 5. Chapitre 2 — Résultats SAST

### 5.1 Semgrep
État actuel (scan CI après corrections) :

| Règle | Sévérité | Nombre |
|---|---|---|
| express-sequelize-injection | ERROR | 6 |
| code-string-concat | ERROR | 1 |
| express-check-directory-listing | WARNING | 5 |
| express-res-sendfile | WARNING | 4 |
| aws-subnet-has-public-ip-address (extraits pédagogiques) | WARNING | 3 |
| insecure-load-balancer-tls-version (extraits pédagogiques) | WARNING | 3 |
| express-open-redirect | WARNING | 1 |
| jwt-hardcode (secret JWT codé en dur) | SECRET | 1 |
| dependabot-missing-cooldown | MEDIUM | 3 |
| github-actions-mutable-action-tag | — | 0 (corrigé) |
| **Total** | | **27** |

Évolution : 6 constats corrigés à l'étape 10 (2 sous-réseaux AWS avec IP publique, 2 écouteurs TLS en HTTP, 2 configuration npm) ; les constats `github-actions-mutable-action-tag` du workflow éliminés par épinglage SHA ; 3 constats `dependabot-missing-cooldown` (MEDIUM, informatifs) apparus avec l'évolution du pack de règles. Les constats restants relèvent du code vulnérable intentionnel d'OWASP Juice Shop et des extraits pédagogiques `data/static/codefixes/` (voir `docs/CORRECTIONS.md`).

### 5.2 SonarQube (local, Docker)
SonarQube Community 9.9.8 (Docker Compose) + sonar-scanner 8.1, projet `juice-shop-workshop2`, analyse réussie (environ 2 min 30).

| Mesure | Valeur |
|---|---|
| Lignes de code (ncloc) | « À COMPLÉTER » |
| Bugs | « À COMPLÉTER » |
| Vulnérabilités | « À COMPLÉTER » |
| Code Smells | « À COMPLÉTER » |
| Security Hotspots | « À COMPLÉTER » |

### 5.3 Comparaison des deux outils
| Critère | Semgrep | SonarQube |
|---|---|---|
| Approche | correspondance de motifs (règles OWASP) | analyseur sémantique et modèle de qualité |
| Règles | pack figé `p/owasp-top-ten` (180 règles) | profil SonarWay (par défaut) |
| Périmètre | TypeScript, Terraform, configuration npm | sources TypeScript filtrées |
| Total des constats | 27 | « À COMPLÉTER » |
| Points forts | rapide, règles OWASP, secrets, IaC | qualité + sécurité, dashboard, hotspots |
| Limites | faux positifs, pas d'analyse de flux | peu de règles de vulnérabilité en édition Community |

### 5.4 Pourquoi les outils diffèrent
1. Objectifs différents : Semgrep recherche des vulnérabilités précises (motifs OWASP Top 10) ; SonarQube mesure surtout la qualité du code, l'analyse de flux « taint » étant réservée aux éditions payantes.
2. Périmètres différents : Semgrep analyse aussi l'infrastructure (Terraform) et la configuration npm, d'où des constats IaC et supply chain que SonarQube ne produit pas.
3. Règles maintenues indépendamment : les packs Semgrep et les profils SonarWay évoluent séparément ; les comptes ne seront donc jamais identiques.
4. Complémentarité : aucun outil ne couvre tout ; la bonne pratique DevSecOps est d'additionner les résultats puis de les arbitrer.

## 6. Chapitre 3 — Résultats SCA

### 6.1 npm audit
Dépôt racine : 26 vulnérabilités (13 faibles, 3 modérées, 10 élevées). Frontend : 20 vulnérabilités (13 faibles, 5 modérées, 2 élevées). `npm audit fix` n'a volontairement pas été appliqué : il corrigerait les vulnérabilités volontaires du projet cible.

### 6.2 OWASP Dependency-Check (CI)
Exécuté sur les deux lockfiles avec le Node Audit Analyzer ; base NVD mise en cache ; clé API NVD via secret GitHub ; archives de test malveillantes exclues (`test/files/` : exemples d'attaques volontaires, pas des dépendances).
- Vulnérabilités détectées : 5 CRITICAL (CVSS ≥ 9), 8 HIGH (CVSS 7.0–8.9), 35 MEDIUM/LOW — 48 occurrences au total.
- Rapport HTML/JSON : artefact `dependency-check-report` (captures 04 et 09).

### 6.3 Dependabot
Activé pour npm (racine et frontend) et github-actions, mises à jour hebdomadaires.
- Alertes de sécurité (onglet Security) : « À COMPLÉTER »
- Politique : les pull requests de mise à jour restent ouvertes comme preuve mais ne sont jamais fusionnées ; elles corrigeraient les vulnérabilités volontaires du projet et fausseraient les résultats SCA (voir l'incident #10/#11 de la section 3).

## 7. Politique du security gate
Le gate (`scripts/security_gate.py`) lit les rapports SAST et SCA et termine le build avec le code 0 (vert) ou 1 (bloqué).
- Règle absolue : un rapport manquant ou illisible = GATE BLOQUANT (exit 1). Un pipeline sans preuve ne passe jamais au vert.
- Seuils « baseline figée » :

| Metrique | Seuil | Mesuré à la figée | État actuel |
|---|---|---|---|
| CRITICAL (Semgrep ERROR + CVE CVSS ≥ 9) | max 12 | 12 | 12 |
| HIGH (Semgrep WARNING + CVE CVSS 7.0–8.9) | max 28 | 28 | 24 |
| Secrets commits | max 1 | 1 | 1 |
| MEDIUM/LOW | informatif | 35 | 38 |

- Ces seuils sont figés une fois pour toutes. Ne jamais les relever pour obtenir un build vert : si le gate est rouge, on corrige le code (voir `docs/CORRECTIONS.md`) ou on accepte le rouge. OWASP Juice Shop est volontairement vulnérable ; une politique absolue resterait rouge à jamais, la baseline garantit qu'aucune régression n'entre.
- Exemple vécu : le gate a bloqué le pipeline sur nos propres actions GitHub non épinglées (HIGH à 35 contre 28) ; l'épinglage aux empreintes SHA a ramené le build au vert sans toucher aux seuils (capture 05 puis 06).

## 8. Corrections apportées
Détail complet dans `docs/CORRECTIONS.md` : sous-réseaux AWS sans IP publique, écouteur de load balancer en HTTP (redirection 301 vers HTTPS), délai minimal npm (`min-release-age = 7`), épinglage des actions GitHub aux empreintes SHA, annulation des fusions Dependabot accidentelles, hygiène des lockfiles.

## 9. Captures d'écran
| Fichier | Contenu |
|---|---|
| `docs/screenshots/01-pipeline-ensemble.png` | les 4 jobs du pipeline, tous verts |
| `docs/screenshots/02-build-tests.png` | job `build-and-test` : compilation sans erreur |
| `docs/screenshots/03-semgrep-findings.png` | constats Semgrep dans la CI |
| `docs/screenshots/04-dependency-check-cve.png` | CVE (GHSA/CVSS) du rapport Dependency-Check |
| `docs/screenshots/05-gate-fail.png` | security gate bloquant (GATE BLOQUANT) |
| `docs/screenshots/06-gate-pass.png` | security gate vert après corrections (GATE PASSE) |
| `docs/screenshots/07-sonarqube-dashboard.png` | tableau de bord SonarQube |
| `docs/screenshots/08-dependabot-alerte.png` | alertes Dependabot (onglet Security) |
| `docs/screenshots/09-rapport-dependency-check.png` | vue d'ensemble du rapport Dependency-Check |
