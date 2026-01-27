# YAGATI Decisions — Journal des Décisions

**Format** : décisions résumées, datées, avec rationale

---

## 2026-01-27 : Context Pack Strategy

**Décision** : Mise en place de la stratégie "Context Pack"

**Rationale** :
- Éviter les conversations GitHub trop lourdes
- Améliorer la continuité du projet entre sessions
- Externaliser le contexte de conversation dans des documents dédiés

**Implémentation** :
- Création de `YAGATI_KERNEL.md` : source de vérité stable
- Création de `YAGATI_STATE.md` : snapshot actuel (<120 lignes)
- Création de `YAGATI_DECISIONS.md` : journal des décisions (ce fichier)
- Création de `YAGATI_CONTEXT_PACK.md` : bootstrap copiable pour nouveaux chats (<120 lignes)
- Ajout section "Bootstrap d'un nouveau chat" dans README.md

**Impact** :
- Documentation plus structurée et maintenable
- Onboarding facilité pour nouveaux contributeurs
- Contexte projet clair et concis

---

## 2026-01-XX : CoinGecko Native OHLC Integration

**Décision** : Intégration native de CoinGecko /ohlc endpoint via Supabase

**Rationale** :
- Données OHLC historiques fiables et gratuites
- Élimination de dépendances tierces instables
- Amélioration de la qualité des données de marché

**Implémentation** :
- Endpoint Supabase exposant CoinGecko /ohlc
- Brain v2 consomme ces données pour l'analyse
- Remplacement de l'ancienne source Supabase market-data

**Impact** :
- Fiabilité accrue des données
- Pas de coût supplémentaire (CoinGecko gratuit)
- Pipeline de données simplifié

---

## 2026-01-XX : Universe Builder Implementation

**Décision** : Création du Universe Builder pour génération déterministe de l'univers tradable

**Rationale** :
- Dépendance Supabase market-data cassée et non fiable
- Besoin d'une liste canonique de symboles tradables
- Déterminisme : mêmes inputs → mêmes outputs

**Implémentation** :
- Module `brain_v2/universe/`
- Sources : CoinGecko (top N market cap) ∩ Bitget (USDT Perp markets)
- Filtrage des stablecoins (USDT, USDC, DAI, etc.)
- Output : top 50 symboles dans `/opt/yagati/data/universe_usdt_perp.json`
- 31 tests unitaires et d'intégration

**Caractéristiques** :
- Déterministe
- APIs publiques uniquement (pas de clés API)
- Logging complet et transparent
- Pas d'écriture Airtable (génération pure de données)

**Impact** :
- Univers tradable fiable et reproductible
- Indépendance vis-à-vis de Supabase market-data
- Base solide pour Brain v2

---

## 2026-01-XX : Brain v1 Quarantine

**Décision** : Mise en quarantaine de Brain v1 (legacy_brain_v1/)

**Rationale** :
- **Violation de sécurité** : credentials hardcodés dans le code
- **Architecture non-déterministe** : comportement imprévisible
- **Superseded par Brain v2** : nouvelle implémentation propre et déterministe

**Actions** :
- Déplacement dans `legacy_brain_v1/`
- Marquage comme OBSOLÈTE
- Interdiction d'utilisation et de modification
- Conservation pour audit uniquement
- Suppression prévue après validation complète de Brain v2

**Impact** :
- Élimination des risques de sécurité
- Focus sur Brain v2 uniquement
- Clarification de l'état du code

---

## 2026-01-XX : Brain v2 Production Adoption

**Décision** : Brain v2 devient le module de production actif

**Rationale** :
- Architecture propre et déterministe
- Pas de credentials hardcodés (env vars uniquement)
- Gouvernance et logging complets
- Intégrations Airtable et Telegram opérationnelles

**Fonctionnalités Brain v2** :
- Détection de setups (forming only)
- Universe Builder intégré
- Logging Airtable (`brain_logs`, `setups_forming`)
- Notifications Telegram
- Données réelles (Supabase + CoinGecko)

**Impact** :
- Module de production fiable et auditable
- Base pour développements futurs (Signal Center, /day, Paper Trading, Bitget Execution)

---

## 2026-01-XX : Pipeline Architecture Decision

**Décision** : Adoption du pipeline de trading suivant

**Pipeline** :
```
Signaux → Signal Center → /day → Paper Trading → Bitget
```

**Rationale** :
- **Signaux** : Brain v2 détecte des setups de marché
- **Signal Center** : agrégation et validation des signaux (à développer)
- **/day** : décisions de trading quotidiennes (à développer)
- **Paper Trading** : simulation avant exécution réelle (à développer)
- **Bitget** : exécution sur exchange (à développer)

**Contraintes** :
- Pas de Binance (conformité)
- Pas de WebSockets (polling REST uniquement)
- Pas de fake data (données réelles uniquement)

**Impact** :
- Roadmap claire pour le développement
- Séparation des responsabilités
- Sécurité via Paper Trading avant prod

---

## 2026-01-XX : Priorités Trading (EV, Drawdown, Risk-of-Ruin)

**Décision** : Hiérarchie des priorités pour le trading

**Ordre de priorité** :
1. **Expected Value (EV)** : rentabilité théorique long terme
2. **Drawdown** : contrôle de la perte maximale
3. **Risk of Ruin** : probabilité de faillite (doit être ~0%)

**Rationale** :
- EV+ est requis pour tout trading
- Drawdown control protège le capital
- Risk-of-ruin minimisé pour éviter la faillite

**Impact** :
- Toute stratégie doit démontrer EV+
- Monitoring continu du drawdown
- Sizing de position ajusté pour minimiser risk-of-ruin

---

## 2026-01-XX : Governance > Speed

**Décision** : La gouvernance prime sur la vitesse

**Principes** :
- Toute modification → PR (jamais de hotfix)
- Pas d'optimisation automatique sans revue
- Documentation synchronisée avec le code
- Audit trail complet via GitHub

**Workflow** :
1. ChatGPT décide (direction, approches)
2. Copilot code via PR (implémentation)
3. GitHub = source de vérité (repository canonique)
4. Confirmé = décision (PR merged ou confirmation explicite)

**Impact** :
- Traçabilité complète
- Réduction des erreurs
- Collaboration efficace
- Qualité > rapidité

---

## 2026-01-XX : GitHub as Single Source of Truth

**Décision** : GitHub est la source unique de vérité

**Rationale** :
- Code, documentation, décisions vivent exclusivement sur GitHub
- Pas de Notion, Google Docs, ou autre source externe
- Repository = état canonique du projet

**Contraintes** :
- Toute décision doit être documentée dans le repo
- Toute modification passe par PR
- Pas de décision en dehors de GitHub

**Impact** :
- Source de vérité centralisée
- Audit trail complet
- Collaboration facilitée

---

## 2026-01-XX : Workflow SWING vs DAY

**Décision** : Séparation stricte entre travaux SWING (long-terme) et DAY (quotidien)

**Définitions** :
- **SWING** : changements structurels, long terme, impact majeur
- **DAY** : changements opérationnels, court terme, impact mineur

**Implémentation** :
- Branches dédiées : `swing/*` et `day/*`
- Labels PR distincts
- Descriptions PR explicites (SWING ou DAY)

**Rationale** :
- Clarté de l'intention
- Revue adaptée au scope
- Isolation des changements

**Impact** :
- Meilleure organisation du travail
- Revue de code plus efficace
- Risque réduit de régression

---

**YAGATI Decisions** — Journal des décisions au 2026-01-27
