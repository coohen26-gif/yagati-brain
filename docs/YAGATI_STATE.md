# YAGATI State — Snapshot Actuel

**Dernière mise à jour** : 2026-01-27

## Modules

**Brain v2 (PRODUCTION)** ✅
- Path : `brain_v2/` | Run : `python brain_v2/run.py`
- Features : détection setups, Universe Builder (50 symboles), logging Airtable (`brain_logs` + `setups_forming`), notifs Telegram, données réelles (Supabase + CoinGecko OHLC)

**Brain v1 (QUARANTINÉ)** ⚠️
- Path : `legacy_brain_v1/` | Status : OBSOLÈTE, ne pas utiliser
- Raison : credentials hardcodés, non-déterministe | Action : conservé pour audit uniquement

**Universe Builder** ✅
- Path : `brain_v2/universe/` | Run : `python3 -m brain_v2.universe.build_universe`
- Fonction : génération déterministe univers tradable (CoinGecko top N ∩ Bitget USDT Perp)
- Output : `/opt/yagati/data/universe_usdt_perp.json` (50 symboles max)

## Intégrations

**Données Marché**
- Supabase : backend API, OHLC via CoinGecko native
- CoinGecko : top crypto market cap, OHLC historiques
- Bitget : marchés USDT Perp (Universe Builder + future exécution)

**Monitoring**
- Airtable : `brain_logs` (heartbeat/scans/observations), `setups_forming` (setups détectés, dédup par symbol/timeframe/setup_type)
- Telegram : notifications temps réel

## Pipeline

**État** : phase 1 (détection setups uniquement)
```
Signaux (Brain v2) → [Signal Center] → [/day] → [Paper Trading] → [Bitget]
```
- ✅ Signaux (Brain v2 détecte setups)
- 🔄 Signal Center, /day, Paper Trading, Bitget Execution (à dev)

**Prochaines étapes** : Signal Center → /day → Paper Trading → Bitget Execution

## Environnement

**Vars** : `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`
**Fichiers** : `.env` (credentials), `.env.example`, `brain_v2/config/settings.py`, `brain_v2/config/symbols.py`

## Tests

**Coverage** : Universe Builder (31 tests mocked), Brain v2 (tests intégration Airtable, détection setups)
**Commandes** :
- Universe Builder : `python3 -m unittest discover -s tests/universe -p 'test_*.py' -v`
- Brain v2 : `python3 -m brain_v2.test_integration`

## Décisions Récentes

**2026-01-27 : Context Pack Strategy** - 4 docs (Kernel, State, Decisions, Context Pack), section README "Bootstrap nouveau chat"
**2026-01-XX : CoinGecko Native OHLC** - OHLC direct CoinGecko via Supabase backend
**2026-01-XX : Universe Builder** - génération déterministe univers (top 50 crypto)
**2026-01-XX : Quarantaine Brain v1** - credentials hardcodés, non-déterministe → Brain v2 prod

## Scope

**Implémenté** ✅ : Détection setups, Universe Builder, logging Airtable, notifs Telegram, données réelles, gouvernance
**À Développer** 🔄 : Signal Center, /day, Paper Trading, Bitget Execution, Backtesting, Risk Management

## Contraintes

**Interdictions** : ❌ Binance, ❌ Fake Data, ❌ WebSockets, ❌ Hotfix, ❌ Auto-optimisation
**Contraintes** : Déterminisme absolu, GitHub source unique, Copilot→PR, Gouvernance > vitesse

## Priorités

**Court Terme** : Signal Center → /day → Paper Trading
**Moyen Terme** : Bitget Execution, Risk Management, Backtesting
**Gouvernance** : Maintenir Context Pack, documenter décisions, sync doc/code

---
**YAGATI State** — Snapshot au 2026-01-27
