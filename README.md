# Workshop 2 DevSecOps — SAST et SCA sur OWASP Juice Shop (Groupe 8)

## 1. Objectif
Mettre en place une chaîne DevSecOps sur une application volontairement vulnérable (OWASP Juice Shop v20.3.0, licence MIT) : analyse statique de code (SAST), analyse de composition logicielle (SCA), intégration continue avec GitHub Actions et security gate. Ce README est le rapport du workshop ; il est complété au fil des étapes.

## 2. Équipe et rôles
| Personne | Rôle |
|---|---|
| OuzzikiLhoussaine (responsable du dépôt) | Rôle A (Semgrep, SonarQube) + Rôle B (Dependency-Check, Dependabot) + Rôle C (pipeline, security gate, rapport) pour ce workshop |
| ZinebHajaj | Collaboratrice : revue des pull requests |
| HasnaEL10 | Collaboratrice : revue des pull requests |

## 3. Organisation du dépôt
- `main` : page d'index uniquement (aucun merge depuis les branches de travail).
- `workshop-2-sast-sca` : projet du Workshop 2 (copie d'OWASP Juice Shop v20.3.0).
- `workshop-2/<nom>-<tâche>` : branches de travail ; toute modification passe par une pull request relue vers `workshop-2-sast-sca` (protection de branche activée : 1 approbation requise).

## 4. Outils et pipeline CI
| Couche | Outil | Exécution |
|---|---|---|
| SAST | Semgrep (pack de règles `p/owasp-top-ten`) | local + CI GitHub Actions |
| SAST | SonarQube Community 9.9.8 | local (Docker Compose) |
| SCA | npm audit, OWASP Dependency-Check, Dependabot | local + CI (chapitre 3) |
| CI | GitHub Actions (`devsecops-pipeline.yml`) | GitHub |
| Gate | `scripts/security_gate.py` | CI (étape 13) |

Pipeline actuel (workflow `DevSecOps Pipeline`) : job `build-and-test` (Node 24, `npm ci`, `npm run build`) et job `sast-sca-semgrep` (scan Semgrep, vérification `test -f semgrep-results.json`, upload de l'artefact `semgrep-report`). Déclencheurs : push sur `workshop-2/**` et `workshop-2-sast-sca`, pull request vers `workshop-2-sast-sca`, exécution manuelle.

## 5. Chapitre 2 — Résultats SAST

### 5.1 Semgrep (local et CI)
Commande : `semgrep --config p/owasp-top-ten --json-output=semgrep-results.json --sarif-output=semgrep-results.sarif .`
- Périmètre : 1169 fichiers suivis par Git ; 180 règles exécutées.
- Total : 34 constats avant corrections (30 du tableau ci-dessous + 4 `github-actions-mutable-action-tag` sur le workflow CI) ; 28 constats après les corrections de l'étape 10.

| Règle Semgrep | Nombre |
|---|---|
| sequelize-injection-express (injection via Sequelize) | 6 |
| terraform aws-subnet-has-public-ip-address (IaC) | 5 |
| terraform insecure-load-balancer-tls-version (IaC) | 5 |
| express-check-directory-listing (listing de répertoire) | 5 |
| express-res-sendfile (envoi de fichier) | 4 |
| npm-missing-minimum-release-age (supply chain) | 2 |
| jwt-hardcode (secret JWT codé en dur) | 1 |
| express-open-redirect (redirection ouverte) | 1 |
| code-string-concat (concaténation de chaînes) | 1 |
| github-actions-mutable-action-tag (workflow CI) | 4 |

### 5.2 SonarQube (local, Docker)
- SonarQube Community 9.9.8 via Docker Compose, sonar-scanner 8.1 (conteneur officiel).
- Analyse : ANALYSIS SUCCESSFUL, rapport uploadé en environ 2 min 30.

| Mesure | Valeur |
|---|---|
| Lignes de code (ncloc) | « À COMPLÉTER » |
| Bugs | « À COMPLÉTER » |
| Vulnérabilités | « À COMPLÉTER » |
| Code Smells | « À COMPLÉTER » |
| Security Hotspots | « À COMPLÉTER » |
| Total des constats | « À COMPLÉTER » |

Règles les plus fréquentes : « À COMPLÉTER ».

### 5.3 Tableau comparatif
| Critère | Semgrep | SonarQube |
|---|---|---|
| Approche | correspondance de motifs sur le code source | analyseur sémantique et modèle de qualité |
| Règles | 180, pack figé `p/owasp-top-ten` | profil SonarWay (règles par défaut, évolutives) |
| Périmètre | TypeScript, Terraform, configuration npm (1169 fichiers) | sources TypeScript filtrées (hors tests, YAML, assets) |
| Total des constats | 28 après corrections (34 avant) | « À COMPLÉTER » |
| Constats partagés par les deux outils | « À COMPLÉTER » | « À COMPLÉTER » |
| Uniquement Semgrep | 10 constats IaC (Terraform), âge minimal des releases npm, secret JWT codé en dur | — |
| Uniquement SonarQube | — | « À COMPLÉTER » |

### 5.4 Pourquoi les outils diffèrent
1. Objectifs différents : Semgrep recherche des vulnérabilités précises (motifs OWASP Top 10) tandis que SonarQube mesure surtout la qualité du code (maintenabilité, fiabilité). En édition Community, SonarQube couvre peu de vulnérabilités web (l'analyse de flux « taint » est réservée aux éditions payantes).
2. Périmètres différents : Semgrep a aussi analysé l'infrastructure (Terraform) et la configuration npm, d'où des constats IaC et supply chain que SonarQube ne produit pas (pas d'analyse IaC en Community).
3. Règles maintenues indépendamment : les packs Semgrep et les profils SonarWay évoluent séparément ; les comptes ne seront donc jamais identiques.
4. Complémentarité : aucun outil ne couvre tout. La bonne pratique DevSecOps est d'additionner les résultats, puis de les arbitrer dans l'étape des corrections, plutôt que de choisir un seul outil.

## 6. Chapitre 3 — Resultats SCA (logiciels tiers)

### 6.1 npm audit
npm audit sur le depot racine (Node 24, npm 11) : 26 vulnerabilites (13 faibles, 3 moderees, 10 elevees) dans les dependances d'origine. npm audit fix n'a volontairement pas ete applique pour preserver le comportement du projet.

### 6.2 OWASP Dependency-Check
Execute dans la CI (conteneur owasp/dependency-check:latest, base NVD mise en cache, cle API NVD via secret) sur package-lock.json et frontend/package-lock.json avec le Node Audit Analyzer. Les archives de test malveillantes (test/files) sont exclues : ce sont des exemples d'attaques volontaires, pas des dependances. Rapport HTML/JSON : artefact dependency-check-report de la CI.
- Vulnérabilités détectées : 5 CRITICAL (CVSS ≥ 9), 8 HIGH (CVSS 7.0–8.9), 35 MEDIUM/LOW — 48 occurrences au total, mesurées par `scripts/security_gate.py` (étape 13).

### 6.3 Dependabot
Active (mises a jour hebdomadaires : npm racine, npm frontend, github-actions). Les alertes de securite se consultent dans l'onglet Security du depot.
- Alertes Dependabot : « A COMPLETER »
- Politique : les pull requests de mise a jour de dependances restent ouvertes comme preuve, mais ne sont jamais fusionnees ; elles corrigeraient les vulnerabilites volontaires du projet cible et fausseraient les resultats SCA.


## 7. Politique du security gate

Le gate (`scripts/security_gate.py`) est le point de décision de la pipeline : il lit les rapports SAST (Semgrep) et SCA (OWASP Dependency-Check) et termine le build avec le code 0 (vert) ou 1 (bloqué).

Règle absolue : un rapport manquant ou illisible = GATE BLOQUANT (exit 1). Un pipeline sans preuve ne passe jamais au vert.

Seuils « baseline figée » (niveau de référence mesuré après les corrections de l'étape 10) :

| Metrique | Seuil | Mesuré |
|---|---|---|
| CRITICAL (Semgrep ERROR + CVE CVSS ≥ 9) | max 12 | 12 |
| HIGH (Semgrep WARNING + CVE CVSS 7.0–8.9) | max 28 | 28 |
| Secrets commits | max 1 | 1 (secret JWT du défi — accepté et documenté) |
| MEDIUM/LOW | informatif | 35 |

Ces seuils sont figés une fois pour toutes. Ne jamais les relever pour obtenir un build vert : si le gate est rouge, on corrige le code (voir `docs/CORRECTIONS.md`) ou on accepte le rouge. OWASP Juice Shop est volontairement vulnérable — une politique absolue (0 critique, 5 high, comme le projet de référence) resterait rouge à jamais ; la baseline garantit qu'aucune régression n'entre. Exemple : sans les corrections de l'étape 10, HIGH serait à 32 et le gate serait rouge.

## 8. Corrections apportées
À venir : vulnérabilités choisies et corrigées (détail dans docs/CORRECTIONS.md).

## 9. Captures d'écran
À venir : les neuf captures demandées (étape 15).
