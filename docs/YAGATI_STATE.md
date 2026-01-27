# YAGATI STATE - État Actuel du Système

**Date**: 2026-01-27 | **Version**: v2 PRODUCTION | **Statut**: ✅ OPÉRATIONNEL

## Modules Actifs

**Brain v2** ✅ PRODUCTION | Path: `brain_v2/` | Run: `python brain_v2/run.py`
**Universe Builder** ✅ OPÉRATIONNEL | Path: `brain_v2/universe/` | Tests: 31 passants
**Brain v1** ❌ QUARANTAINE | Path: `legacy_brain_v1/` | Action: NE PAS UTILISER

## Configuration

### Env Variables (via .env)
```
SUPABASE_URL, SUPABASE_ANON_KEY
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
AIRTABLE_API_KEY, AIRTABLE_BASE_ID
```

### Airtable Tables
- **brain_logs**: heartbeat, scan, observation (timestamp, cycle_type, context, status, note)
- **setups_forming**: volatility_expansion, range_break_attempt, trend_acceleration, compression_expansion

## Univers de Trading

**Source**: CoinGecko top 100 ∩ Bitget USDT Perp
**Taille**: ≤50 symboles | **Format**: BTCUSDT, ETHUSDT, etc.
**Exclusions**: Stablecoins (USDT, USDC, DAI...)
**Timeframes**: 1H, 4H, 1D

**Top Symbols**: BTC, ETH, SOL, BNB, XRP, ADA, AVAX, DOGE, DOT, MATIC

## Intégrations APIs

1. **CoinGecko** (public): `/coins/markets` - Top cryptos
2. **Bitget** (public): `/api/mix/v1/market/contracts` - USDT Perp markets
3. **Supabase**: Données marché temps réel
4. **Telegram**: Notifications
5. **Airtable**: Logging & traçabilité

## Workflow

**Branches**: main (prod), swing/* (long-terme), day/* (court-terme)
**Process**: ChatGPT décide → Copilot PR → Review → Merge → GitHub = vérité

## Tests

**Universe Builder**: `python3 -m unittest discover -s tests/universe -p 'test_*.py' -v`
**Coverage**: 31 tests unitaires/intégration, APIs mockées

## Cycle d'Exécution

**Fréquence**: Toutes les 15 minutes
- Heartbeat → Log GLOBAL Airtable
- Scan symboles → Log par symbole
- Détection patterns → Log observations
- Notifications Telegram si nécessaire

## Points d'Attention

**Sécurité**: ✅ Pas credentials en dur, vars env uniquement, Brain v1 quarantainé
**Performance**: ✅ Rate limiting géré, retry backoff, déterminisme garanti
**Maintenance**: ⚠️ Surveiller rate limits CoinGecko, vérifier APIs, monitorer univers

## Dernières Modifications (Janvier 2026)

1. **Universe Builder**: Déploiement complet, remplacement Supabase, 31 tests
2. **Brain v2**: Migration production, Brain v1 quarantainé, Airtable actif
3. **Documentation**: universe_builder.md, OPS.md, README restructuré

## Prochaines Étapes

**Court Terme**: Validation Brain v2, monitoring Airtable
**Moyen Terme**: Extension tests, optimisation setups
**Long Terme**: Multi-exchange, historique univers

---
**État mis à jour**: 2026-01-27 | **Review**: Événement-driven
