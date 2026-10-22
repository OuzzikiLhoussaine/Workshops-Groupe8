# Guide Workshop 2 — SAST & SCA sur OWASP Juice Shop (Groupe 8)

> Journal pas-à-pas du Workshop 2 (analyse statique SAST + analyse de composition SCA,
> cours DevSecOps). Ce document est tenu à jour à chaque étape pour être réutilisé
> comme base de travail dans les workshops suivants.
>
> Projet cible : **OWASP Juice Shop** (Node.js / TypeScript, licence MIT —
> voir le fichier `LICENSE` à la racine, conservé tel quel).

## 1. Décisions d'organisation (validées par le Owner le 22/10/2026)

- **Un workshop = une branche** dans le dépôt `workshops-Groupe8`.
  Le Workshop 2 vit sur la branche `workshop-2-sast-sca`.
- **Soumission Classroom** : le professeur exige un dépôt nommé exactement
  `workshop2-Groupe8`. Décision : tout le travail se fait dans `workshops-Groupe8` ;
  à l'étape 8 seulement, l'état final de la branche `workshop-2-sast-sca` sera recopié
  dans le dépôt existant `workshop2-Groupe8` (après feu vert du Owner). Aucun dépôt
  n'est créé, renommé ou modifié en dehors de `workshops-Groupe8` d'ici là.
- **Rôles** :
  - **A — SAST** (Semgrep local + CI, SonarQube via Docker, comparaison) : OuzzikiLhoussaine
  - **B — SCA** (OWASP Dependency-Check, npm audit, Dependabot) : OuzzikiLhoussaine
  - **C — Pipeline CI / Security Gate / Rapport** (+ revues de PR) : ZinebHajaj et HasnaEL10
- **Date limite Classroom** : pas encore annoncée au démarrage du workshop.

## 2. Workflow Git

- Branches protégées : `main` et `workshop-2-sast-sca` (modifications uniquement par Pull Request,
  1 approbation d'un autre membre requise).
- Branches de travail : `workshop-2/<nom>-<tâche>` (ex. `workshop-2/zineb-semgrep`),
  PR vers `workshop-2-sast-sca`.
- Avant chaque push : `git pull --rebase` (les coéquipiers peuvent avoir poussé des changements).
- La `LICENSE` MIT de Juice Shop est conservée et le projet est crédité dans le `README.md`.
- Aucun secret (clé API, token, mot de passe) dans les fichiers, les commits ou les messages :
  les secrets vivent dans GitHub (Settings → Secrets and variables → Actions).

## 3. État initial vérifié (avant toute modification)

| Élément | Résultat de la vérification |
|---|---|
| `main` | Uniquement `README.md` (index) |
| `workshop-2-sast-sca` | Copie complète de Juice Shop (commit `f85b34e`) |
| Version Node requise | `engines.node = "22 - 26"` dans `package.json` → Node 22 en CI |
| Build | `npm run build` = `build:frontend` (Angular) + `build:server` (`tsc`) |
| `package-lock.json` | **Absent** (racine et `frontend/`) — voir Étape 1 |
| Outillage Workshop 2 | Aucun : pas de `.github/workflows/`, pas de `dependabot.yml`, pas de `scripts/security_gate.py`, pas de `docs/` |
| Collaborateurs | Seul le Owner → ajouter ZinebHajaj et HasnaEL10 (Étape 0) |
| Dépôt de référence | `workshop2-Groupe8` (ancien projet Java) : on réutilise ses idées (`scripts/security_gate.py`, structure du pipeline et du README), pas son code Java |

## 4. Étape 0 — Accès équipe (Owner, interface GitHub)

L'API utilisée par l'assistant n'a pas les droits « Administration » (erreur 403),
ces actions sont donc faites par le **Owner** dans le navigateur :

1. **Settings → Collaborators → Add people** : `ZinebHajaj` et `HasnaEL10`
   (elles doivent accepter l'invitation pour obtenir l'accès *Write*).
2. **Settings → Branches → Add classic branch protection rule**, pour `main` puis
   pour `workshop-2-sast-sca` : *Require a pull request before merging* +
   *Require approvals* = 1.
   (L'option *Require status checks* sera ajoutée à l'Étape 2, quand la CI existera.)

Statut : ⏳ en attente de confirmation du Owner.

## 5. Étape 1 — Lockfiles et vérification « build zéro erreur »

### 5.1 Problème

Sans `package-lock.json` : `npm ci` (installation reproductible en CI) refuse de démarrer
et OWASP Dependency-Check (Étape 5) n'a pas de graphe de dépendances figé à analyser.

### 5.2 Causes racines trouvées (choix du projet amont Juice Shop)

1. `.npmrc` et `frontend/.npmrc` contiennent `package-lock=false` :
   npm a l'**interdiction explicite** de créer un lockfile.
2. `.gitignore` et `frontend/.gitignore` contiennent la règle `package-lock.json` :
   même généré, le fichier resterait invisible pour Git.

### 5.3 Correctifs appliqués (4 fichiers, avec commentaires explicatifs)

- `.npmrc` et `frontend/.npmrc` : `package-lock=false` → `package-lock=true`
- `.gitignore` et `frontend/.gitignore` : ligne `package-lock.json` remplacée par un
  commentaire (« suivi volontairement : reproductibilité CI + analyse SCA »)

### 5.4 Génération des lockfiles

Racine (résolution seule, sans installation ni `postinstall`) :

```
npm install --package-lock-only
```

✅ `package-lock.json` créé (npm 10.9.8, Node 22.22.3).

Frontend — **incident rencontré** : la même commande échoue en ~2 s avec l'erreur exacte :

```
npm error Cannot read properties of null (reading 'edgesOut')
```

Analyse : bug connu du résolveur de **npm 10** (Arborist), déclenché par le champ
`overrides` présent dans `frontend/package.json` (ligne 86). Ce n'est **pas** une erreur
du code de Juice Shop. Le même bug a fait échouer le `npm install` interne du script
`postinstall` racine (confirmé dans le journal npm de l'exécution).

Contournement propre : génération avec **npm 11** via `npx` (rien d'installé globalement,
lockfile au format v3, lisible par npm 10 en mode `ci`) :

```
npx --yes npm@11 install --package-lock-only
```

✅ `frontend/package-lock.json` créé. (Au passage, ce premier `npm audit` signale déjà
26 vulnérabilités dans les dépendances frontend, dont 10 HIGH — documenté à l'Étape 5.)

### 5.5 Validations effectuées

Installation depuis les lockfiles, scripts désactivés (évite le `postinstall` complet) :

```
npm ci --ignore-scripts --no-audit --no-fund
```

Compilation TypeScript du serveur (doit finir avec **zéro erreur**) :

```
npm run build:server
```

Résultats :
- Racine : 1331 paquets installés depuis le lockfile, `tsc` terminé sans erreur ✅
- Frontend : 699 paquets installés par **npm 10.9.8** depuis le lockfile généré par npm 11 ✅
  (preuve que la CI saura le consommer malgré le champ `overrides`)
- `git status` : seuls les fichiers volontaires sont modifiés ; les `package.json` sont intacts ✅

Reste à prouver : le build Angular complet (`npm run build:frontend`, gourmand en RAM)
→ sur les runners GitHub à l'Étape 2.

### 5.6 Points de vigilance pour la CI (Étape 2)

- Le `postinstall` de Juice Shop exécute
  `cd frontend && npm install && npm run build:frontend && (npm run --silent build:server || cd .)` :
  le `|| cd .` **masque les erreurs `tsc`** → la CI devra relancer `npm run build:server`
  explicitement pour prouver « zéro erreur ». Ne jamais faire confiance au `postinstall`.
- En CI, ne pas laisser le `postinstall` lancer `npm install` dans `frontend/` :
  npm 10 re-résoudrait l'arbre et risquerait le bug `edgesOut`.
  Stratégie prévue : `npm ci --ignore-scripts` (racine + frontend) puis builds explicites.

## 6. Étapes suivantes

- ☐ Étape 2 — Pipeline CI (job `build-and-test`) sur GitHub Actions, YAML validé avant chaque push
- ☐ Étape 3 — SAST Semgrep (rôles A) : configs `p/javascript`, `p/typescript`, `p/owasp-top-ten`, `p/secrets` ; sorties JSON + SARIF ; job CI `sast-semgrep`
- ☐ Étape 4 — SonarQube en local (Docker Compose, token utilisateur, `sonar-scanner`) + comparaison Semgrep/SonarQube
- ☐ Étape 5 — SCA (rôle B) : OWASP Dependency-Check (clé NVD ou miroir), `npm audit`, Dependabot npm (`/` et `/frontend`) ; job CI `sca-dependency-check`
- ☐ Étape 6 — Security Gate `scripts/security_gate.py` : échec si rapport manquant ; seuils 0 CRITICAL, ≤ 5 HIGH, 0 secrets (jamais relevés pour « passer au vert ») ; job `security-gate` — le rouge est attendu avant corrections
- ☐ Étape 7 — Corrections d'un ensemble choisi de vulnérabilités, documentées dans `docs/CORRECTIONS.md` → gate réellement vert
- ☐ Étape 8 — `README.md` final (français) + captures 01→09 + préparation de la soumission Classroom

Validation du YAML du pipeline avant chaque push (à partir de l'Étape 2) :

```
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/devsecops-pipeline.yml'))"
```

## 7. Captures d'écran à produire (`docs/screenshots/`)

| Fichier | Où la prendre | Étape |
|---|---|---|
| `01-pipeline-ensemble.png` | GitHub → Actions → page du run (vue des jobs) | 2 (version finale : 8) |
| `02-build-tests.png` | GitHub Actions → job `build-and-test` en vert | 2 |
| `03-semgrep-findings.png` | Terminal local ou job CI `sast-semgrep` | 3 |
| `04-dependency-check-cve.png` | Rapport Dependency-Check (liste des CVE) dans le navigateur ou logs du job | 5 |
| `05-gate-fail.png` | GitHub Actions → job `security-gate` en échec **avant** corrections | 6 |
| `06-gate-pass.png` | GitHub Actions → job `security-gate` en vert **après** corrections (vert réel) | 7 |
| `07-sonarqube-dashboard.png` | Navigateur → interface SonarQube locale, page du projet | 4 |
| `08-dependabot-alerte.png` | GitHub → onglet Security → Dependabot alerts | 5 |
| `09-rapport-dependency-check.png` | Navigateur → rapport HTML Dependency-Check complet | 5 |

## 8. Pièges connus (à ne pas reproduire)

- **YAML invalide** → GitHub exécute **zéro job**. Toujours valider le YAML en local avant de pousser.
- **Faux vert** : un scan qui échoue en silence (`|| true`, `|| cd .`…) ou un rapport manquant
  ne doit **jamais** donner un job vert. Vérifier l'existence de chaque rapport
  (ex. `test -f semgrep-results.json`) et faire échouer le gate si un rapport manque.
- **Semgrep** : ne jamais répéter `--output` ; utiliser `--json-output=...` et `--sarif-output=...`.
- **Clé NVD invalide** (espaces/retours en trop) → le job SCA échoue. Re-saisir le secret
  proprement, ou le retirer pour utiliser le miroir NVD. Tester chaque option avant de s'y fier.
- **Ubuntu / PEP 668** : `pip install` est bloqué → installer Semgrep avec `pipx`.
- **npm 10 + champ `overrides`** (frontend) → bug `edgesOut` à la résolution.
  Contournement : npm 11 via `npx` pour générer le lockfile ; en CI utiliser `npm ci`
  (pas de re-résolution) et éviter le `postinstall` de Juice Shop.
