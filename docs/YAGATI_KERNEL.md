# YAGATI KERNEL - Source de Vérité

**Version**: 2.0  
**Date**: 2026-01-27  
**Statut**: PRODUCTION

---

## Vision

YAGATI est un système de trading brain-first, où les décisions de trading sont prises par un cerveau déterministe et auditable qui analyse les marchés de manière systématique.

---

## Architecture Système

### Modules Actifs

#### Brain v2 (PRODUCTION)
- **Localisation**: `brain_v2/`
- **Statut**: ✅ ACTIF - Utiliser cette implémentation
- **Type**: Module de décision déterministe (MVP)
- **Documentation**: [brain_v2/README.md](../brain_v2/README.md)

**Caractéristiques**:
- Décisions déterministes et auditables
- Données de marché réelles (Supabase API)
- Universe Builder - Génération déterministe de symboles tradables
- Détection de setups (forming uniquement)
- Gouvernance complète & logging
- Intégration Airtable (`brain_logs` + `setups_forming`)
- Pas de credentials en dur (variables d'environnement uniquement)

**Exécution**:
```bash
python brain_v2/run.py
```

#### Brain v1 (QUARANTAINE)
- **Localisation**: `legacy_brain_v1/`
- **Statut**: ❌ OBSOLÈTE - NE PAS UTILISER
- **Raison**: Violations de sécurité, architecture non-déterministe
- **Note**: Conservé uniquement pour audit

---

## Universe Builder

**Module**: `brain_v2/universe/`  
**Version**: 1.0.0  
**Documentation**: [docs/universe_builder.md](universe_builder.md)

### Fonction
Génère une liste canonique de symboles de cryptomonnaies tradables de manière déterministe.

### Processus
1. Récupère top 100 cryptos par capitalisation (CoinGecko)
2. Exclut les stablecoins
3. Intersecte avec Bitget USDT Perpetual Futures
4. Produit ≤50 symboles au format Bitget (ex: `BTCUSDT`, `ETHUSDT`)
5. Écrit dans `/opt/yagati/data/universe_usdt_perp.json`

### Exécution
```bash
python3 -m brain_v2.universe.build_universe
```

### Caractéristiques Clés
- ✅ Déterministe: Mêmes entrées → mêmes sorties
- ✅ APIs publiques uniquement (pas de clés API)
- ✅ Pas d'écriture Airtable
- ✅ Logging complet
- ✅ Tests complets (31 tests unitaires et d'intégration)

---

## Configuration

### Variables d'Environnement Requises

```bash
# Supabase
SUPABASE_URL=<url_du_projet>
SUPABASE_ANON_KEY=<clé_anonyme>

# Telegram
TELEGRAM_BOT_TOKEN=<token_du_bot>
TELEGRAM_CHAT_ID=<id_du_chat>

# Airtable
AIRTABLE_API_KEY=<clé_api>
AIRTABLE_BASE_ID=<id_de_la_base>
```

### Fichier de Configuration
```bash
cp .env.example .env
# Puis éditer .env avec vos credentials
```

---

## Logging & Traçabilité

### Airtable Brain Logs
Table: `brain_logs`

**Types d'événements** (`cycle_type`):
1. **heartbeat**: Confirmation d'exécution du brain (chaque cycle)
   - `context`: "GLOBAL"
   - `status`: "ok"
   - `note`: "initial brain heartbeat"

2. **scan**: Événements de scan de symbole de marché
   - `context`: Symbole de marché (ex: "BTCUSDT", "ETHUSDT")
   - `status`: "ok"
   - `note`: "market scanned"

3. **observation**: Événements de détection de pattern
   - `context`: Symbole de marché
   - `status`: "weak" ou "neutral"
   - `note`: Description du pattern

### Airtable Setups
Table: `setups_forming`

**Fonctionnalités**:
- Déduplication: Un setup par (symbol, timeframe, setup_type)
- Écritures intelligentes: Uniquement sur changements d'état
- Contexte de marché: NORMAL, VOLATILE, PANIC

**Types de setups détectés**:
- `volatility_expansion`: Spike de volatilité
- `range_break_attempt`: Prix près de haut/bas récent
- `trend_acceleration`: Prix anormalement éloigné des moyennes mobiles
- `compression_expansion`: Faible volatilité suivie d'expansion soudaine

---

## Workflow Opérationnel

Référence: [docs/OPS.md](OPS.md)

### Règles d'Équipe
1. **ChatGPT décide**: ChatGPT est responsable des décisions de direction
2. **Copilot code via PR**: Copilot implémente via pull request
3. **GitHub est la source de vérité**: Le repository est l'état canonique
4. **confirmed = décision**: Les changements confirmés deviennent autoritaires
5. **Pas d'auto-optimisation**: Toute optimisation doit être proposée et confirmée
6. **SWING et DAY séparés**: Changements long-terme vs court-terme isolés

---

## Principes de Gouvernance

### Déterminisme
- Toutes les décisions doivent être reproductibles
- Mêmes entrées → mêmes sorties
- Pas de comportement aléatoire ou imprévisible

### Sécurité
- ❌ Pas de credentials en dur dans le code
- ✅ Toujours utiliser variables d'environnement
- ✅ Validation et audit de tous les changements

### Traçabilité
- Tous les événements loggés dans Airtable
- Historique complet des décisions dans GitHub
- Documentation à jour synchronisée avec le code

---

## Structure du Repository

```
yagati-brain/
├── brain_v2/              # Brain YAGATI v2 (PRODUCTION)
├── legacy_brain_v1/       # Brain v1 (QUARANTAINE)
├── brain_day/             # Modules court-terme
├── engine/                # Moteur core
├── universe/              # Builder d'univers
├── tests/                 # Tests automatisés
├── docs/                  # Documentation
│   ├── YAGATI_KERNEL.md       # Ce fichier (source de vérité)
│   ├── YAGATI_STATE.md        # État actuel
│   ├── YAGATI_DECISIONS.md    # Journal de décisions
│   ├── YAGATI_CONTEXT_PACK.md # Bootstrap pour nouveaux chats
│   ├── OPS.md                 # Workflow opérationnel
│   └── universe_builder.md    # Documentation Universe Builder
└── README.md              # Point d'entrée principal
```

---

## Support et Documentation

- **README Principal**: [/README.md](/README.md)
- **Documentation Brain v2**: [/brain_v2/README.md](/brain_v2/README.md)
- **Universe Builder**: [/docs/universe_builder.md](universe_builder.md)
- **Workflow Opérationnel**: [/docs/OPS.md](OPS.md)

---

**YAGATI KERNEL** - Déterministe. Auditable. Transparent.
