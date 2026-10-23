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
- Total : 30 constats.

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
| Total des constats | 30 | « À COMPLÉTER » |
| Constats partagés par les deux outils | « À COMPLÉTER » | « À COMPLÉTER » |
| Uniquement Semgrep | 10 constats IaC (Terraform), âge minimal des releases npm, secret JWT codé en dur | — |
| Uniquement SonarQube | — | « À COMPLÉTER » |

### 5.4 Pourquoi les outils diffèrent
1. Objectifs différents : Semgrep recherche des vulnérabilités précises (motifs OWASP Top 10) tandis que SonarQube mesure surtout la qualité du code (maintenabilité, fiabilité). En édition Community, SonarQube couvre peu de vulnérabilités web (l'analyse de flux « taint » est réservée aux éditions payantes).
2. Périmètres différents : Semgrep a aussi analysé l'infrastructure (Terraform) et la configuration npm, d'où des constats IaC et supply chain que SonarQube ne produit pas (pas d'analyse IaC en Community).
3. Règles maintenues indépendamment : les packs Semgrep et les profils SonarWay évoluent séparément ; les comptes ne seront donc jamais identiques.
4. Complémentarité : aucun outil ne couvre tout. La bonne pratique DevSecOps est d'additionner les résultats, puis de les arbitrer dans l'étape des corrections, plutôt que de choisir un seul outil.

## 6. Chapitre 3 — Résultats SCA
À venir : npm audit, OWASP Dependency-Check, Dependabot.

## 7. Politique du security gate
À venir : seuils, comportement en cas de rapport manquant.

## 8. Corrections apportées
À venir : vulnérabilités choisies et corrigées (détail dans docs/CORRECTIONS.md).

## 9. Captures d'écran
À venir : les neuf captures demandées (étape 15).
