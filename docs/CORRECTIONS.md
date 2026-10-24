# Corrections — Workshop 2 (Chapitre 2 : SAST)

Contexte : après les analyses Semgrep (pack p/owasp-top-ten) et SonarQube, ce document recense les corrections appliquées sans toucher au code vulnérable intentionnel d'OWASP Juice Shop. Après corrections : les 6 constats corrigés ont disparu ; le scan local compte 28 constats Semgrep (7 ERROR, 20 WARNING, 1 secret). Le build reste sans erreur (npm run build).

## Corrections appliquées (6)

### 1. Sous-réseaux AWS sans IP publique (règle aws-subnet-has-public-ip-address)
- Fichiers : terraform/networking.tf et infrastructure/terraform/networking.tf
- Problème : map_public_ip_on_launch = true expose automatiquement les ressources du sous-réseau sur Internet.
- Correction : map_public_ip_on_launch = false.
- Impact : nul pour l'application (ces fichiers décrivent un déploiement AWS non utilisé par l'atelier).

### 2. Écouteur de load balancer en HTTP (règle insecure-load-balancer-tls-version)
- Fichiers : terraform/networking.tf et infrastructure/terraform/networking.tf
- Problème : l'écouteur aws_lb_listener "http" (port 80) transférait le trafic en clair.
- Correction : l'action par défaut devient une redirection 301 vers HTTPS (solution acceptée par la règle). Le trafic chiffré reste porté par l'écouteur HTTPS existant (politique TLS 1.3).
- Impact : nul pour l'application ; aligné sur la pratique TLS everywhere.

### 3. Chaîne d'approvisionnement npm (règle npm-missing-minimum-release-age)
- Fichiers : .npmrc et frontend/.npmrc
- Problème : aucun délai minimal avant l'installation de versions de paquets fraîchement publiées (risque supply chain).
- Correction : ajout de min-release-age = 7 (7 jours), valeur recommandée par la règle. Hygiène connexe : package-lock passe à true dans frontend/.npmrc, par cohérence avec les lockfiles versionnées nécessaires à npm ci et à l'analyse SCA.
- Impact : npm ci (installation verrouillée) inchangé ; lors d'un npm install, npm refuse les versions publiées depuis moins de 7 jours, comportement voulu.

## Constats volontairement non corrigés

- data/static/codefixes (6 constats) : extraits de code des défis pédagogiques de Juice Shop ; le code vulnérable est l'exercice.
- Code applicatif intentionnel (17 constats) : injection SQL (routes/search.ts, routes/login.ts), listing de répertoire (server.ts), envoi de fichier (routes/fileServer.ts, keyServer, logfileServer, quarantineServer), redirection ouverte (routes/redirect.ts), eval (routes/userProfile.ts). Corriger ces fichiers désactiverait les défis correspondants.
- Clé RSA privée codée en dur (lib/insecurity.ts) : elle alimente le défi du JWT contrefait et reste volontairement exposée. En option future : la déplacer vers encryptionkeys/jwt avec chargement par fichier, sans changer le comportement.

## Vérifications
- npm run build : 0 erreur (règle enseignant numéro 2).
- Semgrep après corrections : 28 constats (7 ERROR, 20 WARNING, 1 secret) ; les 6 constats corrigés ont disparu.
- Seuils du security gate : figés à la baseline après calibration (jamais relevés pour obtenir un build vert).
- Aucun secret dans les fichiers, les commits ou les captures d'écran.
