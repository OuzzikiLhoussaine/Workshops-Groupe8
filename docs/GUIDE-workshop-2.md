# Guide de reproduction — Workshop 2 (Groupe 8)

Ce document explique comment refaire, vérifier et maintenir l'atelier 2 (SAST et SCA sur OWASP Juice Shop) à partir d'une machine neuve, puis comment lire les résultats du pipeline.

## 1. Objectif

Mettre en place une chaîne DevSecOps complète sur OWASP Juice Shop : analyse statique (SAST) avec Semgrep et SonarQube, analyse des composants (SCA) avec OWASP Dependency-Check, npm audit et Dependabot, le tout orchestré par un pipeline GitHub Actions qui bloque le build via un security gate.

## 2. Prérequis

- Git, compte GitHub avec droits d'écriture sur le dépôt, CLI `gh` authentifiée
- Node.js 24 (via nvm) et npm 11 — npm 9/10 plantent avec les `overrides` du frontend
- Docker et Docker Compose (SonarQube 9.9.8, image `owasp/dependency-check`)
- Semgrep installé avec `pipx` (jamais `pip` direct : PEP 668 sur Ubuntu récent)
- Un User Token SonarQube (pas un Project Analysis Token) exporté en `$SONAR_TOKEN`

Vérifications :

~~~
source ~/.nvm/nvm.sh ; nvm use 24
~~~
~~~
npm -v
~~~
~~~
pipx list
~~~

Attendu : Node v24.x, npm 11.x, semgrep listé par pipx.

## 3. Organisation du dépôt

- `workshop-2-sast-sca` : branche par défaut, contient le projet et le rapport.
- `main` : README d'index uniquement — règle absolue : ne jamais y importer le projet.
- Branches de tâche : `workshop-2/lhoussaine-<tache>`, puis pull request, revue, fusion.
- `.github/workflows/devsecops-pipeline.yml` : pipeline en 4 jobs, actions épinglées en SHA complet.
- `scripts/security_gate.py` : le security gate (baseline figée).
- `docs/CORRECTIONS.md` : corrections apportées et exclusions assumées.
- `docs/screenshots/` : captures d'écran de preuve (01 à 09).
- `sonarqube/docker-compose.yml` et `sonar-project.properties` : SonarQube local.
- `.github/dependabot.yml` : npm (racine et frontend) + github-actions.
- `.npmrc` : `package-lock=true`, `min-release-age = 7` ; `frontend/.npmrc` : `legacy-peer-deps=true`.

## 4. Pipeline CI (4 jobs)

1. `build-and-test` : installation via lockfiles et compilation TypeScript — zéro erreur de compilation attendue.
2. `sast-sca-semgrep` : scan avec le pack `p/owasp-top-ten`, rapport `semgrep-results.json` + SARIF, contrôle d'existence du rapport.
3. `sca-dependency-check` : image Docker OWASP, base NVD mise en cache (`.dc-data`, clés `dependency-check-nvd2-*`), clé NVD via secret `NVD_API_KEY`, exclusion des archives de test `test/files/`.
4. `security-gate` : télécharge les deux rapports, exécute `scripts/security_gate.py`, vert ou rouge.

Déclenchement : push sur `workshop-2-sast-sca`, ou Actions, puis « Run workflow ». Après un changement de code, toujours lancer un run frais (jamais « Re-run » sur un vieux run : il rejoue l'ancien commit).

Validation systématique de la YAML avant chaque push :

~~~
node -e "require('js-yaml').load(require('fs').readFileSync('.github/workflows/devsecops-pipeline.yml','utf8')); console.log('YAML OK')"
~~~

## 5. SAST en local

### 5.1 Semgrep

~~~
semgrep --config p/owasp-top-ten --json-output=semgrep-results.json --sarif-output=semgrep-results.sarif .
~~~
~~~
test -f semgrep-results.json
~~~

### 5.2 SonarQube (Docker)

~~~
docker start sonarqube sonarqube_db
~~~

Puis, avec `$SONAR_TOKEN` exporté :

~~~
sonar-scanner -Dsonar.projectKey=juice-shop-workshop2 -Dsonar.host.url=http://localhost:9000 -Dsonar.login="$SONAR_TOKEN"
~~~

Attention : `-Dsonar.token` n'existe pas sur 9.9.8 — utiliser `-Dsonar.login`. Tableau de bord : `http://localhost:9000/dashboard?id=juice-shop-workshop2`.

## 6. SCA en local

### 6.1 npm audit

~~~
npm audit
~~~

Jamais `npm audit fix` : cela corrigerait les vulnérabilités volontaires de Juice Shop.

### 6.2 OWASP Dependency-Check

~~~
mkdir -p reports .dc-data
~~~
~~~
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/src:ro -v "$PWD/.dc-data":/usr/share/dependency-check/data -v "$PWD/reports":/reports owasp/dependency-check:latest --scan /src --format JSON --format HTML --project "juice-shop-workshop2" --exclude "**/test/files/**" --nvdApiKey "$NVD_API_KEY" --out /reports/odc
~~~

Points sensibles : `mkdir -p` AVANT `docker run` (sinon Docker crée les dossiers en root et l'analyse échoue, exit 13) ; `--exclude "**/test/files/**"` (archives d'attaques volontaires qui font échouer l'extraction, exit 14) ; `NVD_API_KEY` sans espaces, ou retirer le secret pour utiliser l'API sans clé.

### 6.3 Dependabot

Configuration `.github/dependabot.yml` : npm racine, npm frontend, github-actions, mises à jour hebdomadaires. Politique : les pull requests Dependabot servent de preuve mais ne sont JAMAIS fusionnées (elles corrigeraient les vulnérabilités volontaires du projet — incident #10/#11 documenté dans le README).

## 7. Security gate

~~~
python3 scripts/security_gate.py --semgrep reports/semgrep/semgrep-results.json --odc reports/odc/dependency-check-report.json
~~~

Baseline figée, à ne JAMAIS assouplir : CRITICAL max 12, HIGH max 28, secrets max 1 (MEDIUM et LOW informatifs). Un rapport manquant ou illisible = sortie 1 (gate bloquant). Corriger le code ou accepter le rouge : jamais augmenter les seuils.

## 8. Résultats attendus

| Contrôle | Attendu |
|---|---|
| build-and-test | vert, 0 erreur de compilation |
| Semgrep | 27 constats (7 ERROR, 16 WARNING, 1 SECRET, 3 MEDIUM) |
| Dependency-Check | 5 CRITICAL, 8 HIGH, 35 MEDIUM/LOW (48 occurrences) |
| npm audit | racine 26, frontend 20 (corrections volontairement non appliquées) |
| Security gate | vert (mesuré : 12 CRITICAL, 24 HIGH, 1 secret — plafonds 12/28/1) |

## 9. Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| npm crash `edgesOut` ou `loadPeerSet` | npm 10.9.9 ou moins + `overrides` frontend | installer npm 11 (`npm install -g npm@11`) |
| `externally-managed-environment` (PEP 668) | pip système Ubuntu | `pipx install semgrep` |
| Dependency-Check exit 13 (verrou H2, « No documents exist ») | dossiers créés en root par Docker | `mkdir -p reports .dc-data` avant le run |
| Dependency-Check exit 14 (erreurs zip) | archives d'attaque `test/files/` | `--exclude "**/test/files/**"` |
| SonarQube « Insufficient privileges » | token absent ou Project Analysis Token | User Token exporté en `$SONAR_TOKEN` |
| `-Dsonar.token` refusé | option inconnue sur 9.9.8 | `-Dsonar.login="$SONAR_TOKEN"` |
| SCA KO sans clé NVD valide | clé absente ou espaces dans le secret | saisir `NVD_API_KEY` sans espaces ou retirer le secret |
| Gate rouge « rapport manquant » | artefacts absents | vérifier que les jobs produisent bien les rapports |
| Semgrep `github-actions-mutable-action-tag` | actions épinglées en tag | épingler en SHA complet |
| ERESOLVE stylelint 17 vs 16 | peer deps frontend | `legacy-peer-deps=true` dans `frontend/.npmrc`, ne jamais fusionner la PR Dependabot |

## 10. Règles d'or

1. Valider chaque YAML avant push (commande de la section 4).
2. Jamais de secret dans un fichier, un commit ou un message de chat.
3. Jamais « Re-run » sur un vieux run après un changement de code.
4. Jamais fusionner une pull request Dependabot.
5. Jamais `npm audit fix` sur ce projet.
6. Vérifier la branche de base de chaque pull request avant création (`main` n'est jamais la cible).
7. Seuils du security gate : figés une fois pour toutes.
