# YAGATI Kernel — Source de Vérité

**Version**: 1.0  
**Dernière mise à jour**: 2026-01-27

## Identité du Projet

**YAGATI** = Brain-first trading system

Objectif : système de trading algorithmique basé sur l'analyse de marchés crypto, axé sur la gouvernance, la déterminisme et le contrôle du risque.

---

## Principes Fondamentaux

### 1. GitHub = Source Unique
- **Toute décision confirmée vit dans le dépôt GitHub**
- Le code, la documentation et les décisions existent exclusivement sur GitHub
- Pas de source de vérité externe (Notion, Google Docs, etc.)

### 2. Workflow : Copilot → PR (jamais de hotfix)
- **Toute modification passe par une Pull Request**
- GitHub Copilot propose les changements via PR
- Jamais de modifications directes en production
- Jamais de hotfix sans revue

### 3. Gouvernance > Vitesse
- La rigueur et la traçabilité priment sur la rapidité
- Chaque décision doit être documentée
- Chaque changement doit être auditable
- Pas d'optimisation automatique sans revue

### 4. Déterminisme Absolu
- Comportement prédictible et reproductible
- Mêmes inputs → mêmes outputs
- Pas de randomisation, pas de non-déterminisme
- Auditable à chaque étape

---

## Architecture Pipeline

### Pipeline de Trading (flux obligatoire)

```
Signaux → Signal Center → /day → Paper Trading → Bitget
```

**Détails** :
1. **Signaux** : détection de setups de marché (Brain v2)
2. **Signal Center** : agrégation et validation des signaux
3. **/day** : décisions de trading quotidiennes
4. **Paper Trading** : simulation avant exécution réelle
5. **Bitget** : exécution sur exchange (USDT Perpetual Futures uniquement)

### Interdictions Strictes

❌ **Binance** : interdit (raisons de conformité)  
❌ **Fake Data** : données synthétiques interdites (uniquement données réelles)  
❌ **WebSockets** : interdits (polling API REST uniquement pour stabilité)

---

## Priorités Trading

### Hiérarchie des Priorités

1. **Expected Value (EV)** : rentabilité théorique à long terme
2. **Drawdown** : contrôle de la perte maximale
3. **Risk of Ruin** : probabilité de faillite → doit être proche de 0%

**En pratique** :
- Pas de trading sans EV+ démontré
- Drawdown max surveillé en permanence
- Taille de position ajustée pour minimiser risk-of-ruin

---

## Modules Actifs

### Brain v2 (PRODUCTION)
- **Statut** : ACTIF
- **Path** : `brain_v2/`
- **Rôle** : détection de setups de marché, prise de décision déterministe
- **Features** :
  - Détection de setups (forming only)
  - Universe Builder (top 50 symboles crypto)
  - Logging Airtable (heartbeat, scans, observations)
  - Intégration Telegram (notifications)
  - Données réelles via Supabase & CoinGecko

### Brain v1 (QUARANTINÉ)
- **Statut** : OBSOLÈTE
- **Path** : `legacy_brain_v1/`
- **Raison** : credentials hardcodés, architecture non-déterministe
- **Action** : ne pas utiliser, ne pas modifier, conservé pour audit uniquement

### Universe Builder
- **Statut** : ACTIF
- **Path** : `brain_v2/universe/`
- **Rôle** : génération déterministe de la liste canonique de symboles tradables
- **Output** : top 50 symboles crypto (Bitget USDT Perp uniquement)

---

## Intégrations

### Données de Marché
- **Supabase** : API backend pour données OHLC (CoinGecko native)
- **CoinGecko** : top crypto par market cap, données OHLC
- **Bitget** : marchés USDT Perpetual Futures (pour Universe Builder et exécution)

### Logging & Monitoring
- **Airtable** :
  - Table `brain_logs` : heartbeat, scans, observations
  - Table `setups_forming` : setups détectés (déduplication par symbol/timeframe/setup_type)
- **Telegram** : notifications en temps réel

### Interdictions
- ❌ **Binance** : pas d'utilisation
- ❌ **WebSockets** : polling REST uniquement
- ❌ **Données synthétiques** : real market data uniquement

---

## Workflow Opérationnel (OPS)

### Processus de Décision
1. **ChatGPT décide** : orientation, approches, arbitrages
2. **Copilot code via PR** : implémentation des décisions
3. **GitHub = source de vérité** : repository = état canonique
4. **Confirmé = décision** : PR merged ou confirmation explicite → décision d'équipe
5. **Pas d'auto-optimisation** : toute optimisation doit être proposée, revue, confirmée
6. **SWING et DAY séparés** : branches et labels distincts pour long-terme vs court-terme

### Branches & PR
- **Format branches** : `swing/*` ou `day/*` selon impact
- **Labels PR** : clairement identifiés (SWING ou DAY)
- **Descriptions PR** : explicites sur l'intention et le scope

---

## Environnement & Configuration

### Variables d'Environnement Requises
- `SUPABASE_URL` : URL projet Supabase
- `SUPABASE_ANON_KEY` : clé anonyme Supabase
- `TELEGRAM_BOT_TOKEN` : token bot Telegram
- `TELEGRAM_CHAT_ID` : chat ID Telegram
- `AIRTABLE_API_KEY` : clé API Airtable
- `AIRTABLE_BASE_ID` : base ID Airtable

### Fichiers de Configuration
- `.env` : credentials (jamais commité, utiliser `.env.example`)
- `brain_v2/config/settings.py` : paramètres globaux
- `brain_v2/config/symbols.py` : configuration symboles

---

## Tests & Qualité

### Exigences
- Tests unitaires pour toute nouvelle feature
- Tests d'intégration pour pipelines critiques
- Pas de modification sans validation

### Commandes de Test
```bash
# Universe Builder tests
python3 -m unittest discover -s tests/universe -p 'test_*.py' -v

# Brain v2 integration tests
python3 -m brain_v2.test_integration
```

---

## Gouvernance

### Règles de Changement
1. Toute modification → PR
2. PR doit être revue avant merge
3. Pas de hotfix direct
4. Documentation synchronisée avec le code
5. Décisions documentées dans `YAGATI_DECISIONS.md`

### Rôles
- **ChatGPT** : décision & direction
- **Copilot** : implémentation & PR
- **GitHub** : source de vérité & audit trail

---

## Références

- **README** : `/README.md`
- **OPS** : `/docs/OPS.md`
- **Universe Builder** : `/docs/universe_builder.md`
- **Brain v2** : `/brain_v2/README.md`

---

**YAGATI Kernel** — Déterministe. Gouverné. Auditable.
