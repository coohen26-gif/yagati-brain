# YAGATI CONTEXT PACK - Bootstrap pour Nouveau Chat

**Version**: 1.0 | **Date**: 2026-01-27 | **Usage**: Copier au début de toute nouvelle session

## 🎯 Contexte

**YAGATI** = Système trading brain-first, architecture déterministe et auditable

**Brain Actif**: v2 PRODUCTION (`brain_v2/`) | **Brain Obsolète**: v1 QUARANTAINE (`legacy_brain_v1/`) ❌

## 📁 Structure

```
yagati-brain/
├── brain_v2/           # PRODUCTION ✅
├── legacy_brain_v1/    # QUARANTAINE ❌
├── docs/               # KERNEL, STATE, DECISIONS, CONTEXT_PACK
└── README.md
```

## ⚡ Commandes

```bash
python brain_v2/run.py                              # Exécuter Brain v2
python3 -m brain_v2.universe.build_universe         # Générer univers
cp .env.example .env                                 # Config
```

## 🔑 Env Variables

```
SUPABASE_URL, SUPABASE_ANON_KEY
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
AIRTABLE_API_KEY, AIRTABLE_BASE_ID
```

## 📊 Airtable

**brain_logs**: heartbeat, scan, observation
**setups_forming**: volatility_expansion, range_break_attempt, trend_acceleration, compression_expansion

## 🎯 Universe Builder

`brain_v2/universe/` - Liste déterministe symboles tradables
1. Top 100 CoinGecko → 2. Exclut stablecoins → 3. ∩ Bitget USDT Perp → 4. Output ≤50 symboles
Output: `/opt/yagati/data/universe_usdt_perp.json`

## 🛡️ Règles

1. **Déterminisme**: Mêmes entrées → mêmes sorties
2. **Sécurité**: Jamais credentials en dur
3. **Traçabilité**: Tout loggé Airtable
4. **GitHub**: Source de vérité
5. **Brain v1**: ❌ NE JAMAIS UTILISER

## 👥 Workflow

ChatGPT décide → Copilot PR → Review → Merge → GitHub vérité
**Branches**: main (prod), swing/* (long-terme), day/* (court-terme)
**Référence**: [docs/OPS.md](OPS.md)

## 📚 Documentation

- **KERNEL**: [YAGATI_KERNEL.md](YAGATI_KERNEL.md) - Source vérité système
- **STATE**: [YAGATI_STATE.md](YAGATI_STATE.md) - État actuel
- **DECISIONS**: [YAGATI_DECISIONS.md](YAGATI_DECISIONS.md) - Journal décisions
- **OPS**: [OPS.md](OPS.md) - Workflow
- **Universe**: [universe_builder.md](universe_builder.md) - Doc technique

## ⚠️ Points Critiques

**À FAIRE** ✅: Brain v2, consulter docs, tester, logger Airtable
**À ÉVITER** ❌: Brain v1, credentials en dur, modifs sans tests, auto-optimisation

## 🔄 Cycle (15 min)

1. Heartbeat → Log GLOBAL
2. Scan symboles → Log/symbole
3. Détection patterns → Log observations
4. Telegram notifications

## 🎓 Onboarding

**Nouveau Projet**: CONTEXT_PACK → KERNEL → STATE → OPS → setup .env → test
**Nouveau Chat**: Copier CONTEXT_PACK → STATE updates → DECISIONS historique → continuer

---
**YAGATI CONTEXT PACK** - Dernière màj: 2026-01-27
