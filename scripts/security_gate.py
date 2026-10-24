#!/usr/bin/env python3
"""
Security Gate - Workshop 2 (Groupe 8) - adapte du projet de reference.

Risk acceptance gate des Chapitres 2 (SAST) et 3 (SCA) :

    Build FAIL si :
      - un rapport (Semgrep ou Dependency-Check) est manquant (toujours)
      - le nombre de CRITICAL depasse MAX_CRITICAL
      - le nombre de HIGH depasse MAX_HIGH
      - le nombre de secrets commits depasse MAX_SECRETS
    Build PASS sinon

Politique "baseline figee" : les seuils sont le niveau de reference mesure
APRES les corrections (docs/CORRECTIONS.md). OWASP Juice Shop est
volontairement vulnerable : une politique absolue (0/5/0) resterait rouge
a jamais et ne serait pas informative. Regle absolue : ne JAMAIS relever
les seuils pour obtenir un build vert ; on corrige le code, ou on accepte
un gate rouge.

Lit les rapports produits par les jobs SAST (Semgrep) et SCA
(OWASP Dependency-Check), genere un resume Markdown dans le job summary
GitHub, et bloque (exit 1) si la politique est violee.
"""

import argparse
import json
import os
import sys

# --- Politique de securite (seuils = baseline figee) -----------------
# Composante Semgrep (scan du 24/10/2026 apres corrections Step 10) :
SEMGREP_BASE_CRITICAL = 7    # severity ERROR
SEMGREP_BASE_HIGH = 20    # WARNING (dont 4 github-actions-mutable-action-tag sur le workflow)
SEMGREP_BASE_SECRETS = 1     # regle de type "secret" (secret JWT du defi)
# Composante Dependency-Check (a figer apres calibration) :
ODC_BASE_CRITICAL = 5    # fige le 24-10-2026 : CVE CVSS >= 9.0
ODC_BASE_HIGH = 8    # fige le 24-10-2026 : CVE CVSS 7.0 a 8.9

MAX_CRITICAL = SEMGREP_BASE_CRITICAL + ODC_BASE_CRITICAL
MAX_HIGH = SEMGREP_BASE_HIGH + ODC_BASE_HIGH
MAX_SECRETS = SEMGREP_BASE_SECRETS

critical_count = 0
high_count = 0
medium_low_count = 0
secret_count = 0
details = []


def add_detail(tool, severity, message):
    details.append((tool, severity, message))


def load_report(path, label):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERREUR : rapport {label} introuvable ({path}).")
        add_detail("Pipeline", "MISSING", f"rapport {label} introuvable")
        return None
    except json.JSONDecodeError:
        print(f"ERREUR : rapport {label} illisible ({path}).")
        add_detail("Pipeline", "MISSING", f"rapport {label} illisible")
        return None


def main():
    global critical_count, high_count, medium_low_count, secret_count
    parser = argparse.ArgumentParser(description="Security Gate Workshop 2 (Groupe 8)")
    parser.add_argument("--semgrep", default="reports/semgrep/semgrep-results.json")
    parser.add_argument("--odc", default="reports/odc/dependency-check-report.json")
    args = parser.parse_args()

    # --- 1. Analyse du rapport Semgrep (SAST) ---
    data = load_report(args.semgrep, "Semgrep")
    if data is not None:
        for r in data.get("results", []):
            check_id = r.get("check_id", "")
            severity = (r.get("extra", {}).get("severity") or "INFO").upper()
            location = f"{r.get('path')}:{r.get('start', {}).get('line', '?')}"
            is_secret = "secret" in check_id.lower()
            if is_secret:
                secret_count += 1
                add_detail("Semgrep", "SECRET", f"{location} - {check_id}")
            elif severity == "ERROR":
                critical_count += 1
                add_detail("Semgrep", "CRITICAL", f"{location} - {check_id}")
            elif severity == "WARNING":
                high_count += 1
                add_detail("Semgrep", "HIGH", f"{location} - {check_id}")
            else:
                medium_low_count += 1
                add_detail("Semgrep", "MEDIUM/LOW", f"{location} - {check_id}")

    # --- 2. Analyse du rapport OWASP Dependency-Check (SCA) ---
    data = load_report(args.odc, "Dependency-Check")
    if data is not None:
        for dep in data.get("dependencies", []):
            for v in (dep.get("vulnerabilities") or []):
                name = v.get("name", "?")
                score = 0.0
                cvss3 = v.get("cvssv3") or {}
                if isinstance(cvss3, dict):
                    score = float(cvss3.get("baseScore") or 0)
                elif isinstance(v.get("cvssv2"), dict):
                    score = float(v["cvssv2"].get("baseScore") or 0)
                pkg = (dep.get("packages") or [{}])[0].get("id", dep.get("fileName", "?"))
                msg = f"{name} (CVSS {score}) sur {pkg}"
                if score >= 9.0:
                    critical_count += 1
                    add_detail("Dependency-Check", "CRITICAL", msg)
                elif score >= 7.0:
                    high_count += 1
                    add_detail("Dependency-Check", "HIGH", msg)
                else:
                    medium_low_count += 1
                    add_detail("Dependency-Check", "MEDIUM/LOW", msg)

    # --- 3. Decision (gate) ---
    missing_reports = any(tool == "Pipeline" for tool, _, _ in details)

    # Un rapport manquant = FAIL (sinon un scan en echec passerait au vert)
    failed = (
        missing_reports
        or critical_count > MAX_CRITICAL
        or high_count > MAX_HIGH
        or secret_count > MAX_SECRETS
    )

    summary = [
        "## \U0001f6e1\ufe0f Security Gate - Resultat",
        "",
        "| Metrique | Nombre | Politique |",
        "|---|---|---|",
        f"| CRITICAL | {critical_count} | max {MAX_CRITICAL} |",
        f"| HIGH | {high_count} | max {MAX_HIGH} |",
        f"| MEDIUM/LOW | {medium_low_count} | informatif |",
        f"| Secrets commits | {secret_count} | max {MAX_SECRETS} |",
        "",
    ]

    if details:
        summary.append("### \U0001f4cb Details des findings")
        summary.append("")
        summary.append("| Outil | Severite | Finding |")
        summary.append("|---|---|---|")
        for tool, sev, msg in details[:40]:
            summary.append(f"| {tool} | {sev} | {msg.replace('|', '/')} |")
        if len(details) > 40:
            summary.append(f"\n_(... {len(details) - 40} autres findings dans les artefacts)_")
        summary.append("")

    if failed:
        summary.append("### \u274c GATE BLOQUANT")
        summary.append("Le niveau de risque est **inacceptable** : corrigez les vulnerabilites "
                       "(voir `docs/CORRECTIONS.md`), puis poussez un nouveau commit "
                       "pour relancer automatiquement le pipeline (Shift Left).")
    else:
        summary.append("### \u2705 GATE PASSE")
        summary.append("Niveau de risque dans la politique (baseline figee) : le build peut continuer.")

    report = "\n".join(summary)
    print(report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(report + "\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
