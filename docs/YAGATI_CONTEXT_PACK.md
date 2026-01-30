# YAGATI Context Pack — Bootstrap Nouveau Chat

**Version** : 1.0 | **Mis à jour** : 2026-01-27

## Identité
**YAGATI** = Brain-first trading system (crypto algo, gouvernance stricte, déterministe)

## Règles Absolues
- **GitHub = source unique** : toute décision/code/doc vit exclusivement sur GitHub
- **Copilot → PR, jamais hotfix** : toute modif passe par PR, pas de changement direct
- **Gouvernance > vitesse** : rigueur et traçabilité priment sur rapidité
- **Déterminisme absolu** : mêmes inputs → mêmes outputs, comportement reproductible

## Pipeline Trading
```
Signaux → Signal Center → /day → Paper Trading → Bitget
```
- Signaux : Brain v2 détecte setups | Signal Center : agrégation/validation (à dev) | /day : décisions quotidiennes (à dev) | Paper Trading : simulation (à dev) | Bitget : exécution USDT Perp (à dev)

## Interdictions
❌ Binance (conformité) | ❌ Fake Data | ❌ WebSockets (polling REST uniquement) | ❌ Hotfix (PR obligatoire) | ❌ Auto-optimisation (revue requise)

## Priorités Trading
1. **EV (Expected Value)** : EV+ requis | 2. **Drawdown** : contrôle perte max | 3. **Risk-of-Ruin** : ~0%

## Modules

**Brain v2** ✅ (PROD) : `brain_v2/` | `python brain_v2/run.py` | Features : détection setups, Universe Builder, logging Airtable, notifs Telegram, données réelles

**Brain v1** ⚠️ (QUARANTINÉ) : `legacy_brain_v1/` | OBSOLÈTE, ne pas utiliser/modifier | Raison : credentials hardcodés, non-déterministe

**Universe Builder** ✅ : `brain_v2/universe/` | `python3 -m brain_v2.universe.build_universe` | Top 50 crypto (CoinGecko ∩ Bitget USDT Perp) → `/opt/yagati/data/universe_usdt_perp.json`

## Intégrations

**Marché** : Supabase (OHLC via CoinGecko), CoinGecko (market cap, OHLC), Bitget (USDT Perp)
**Monitoring** : Airtable (`brain_logs`, `setups_forming`), Telegram (notifs temps réel)

## Workflow OPS
1. ChatGPT décide | 2. Copilot code via PR | 3. GitHub = source vérité | 4. Confirmé = décision | 5. Pas auto-optimisation | 6. SWING vs DAY séparés (`swing/*`, `day/*`)

## Env Vars
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`

## État (2026-01-27)

**Implémenté** ✅ : Brain v2 prod, Universe Builder (50 symboles), logging Airtable, notifs Telegram, données réelles (Supabase + CoinGecko OHLC)
**À Dev** 🔄 : Signal Center, /day, Paper Trading, Bitget Execution, Risk Management, Backtesting

## Commandes
```bash
python brain_v2/run.py  # Brain v2
python3 -m brain_v2.universe.build_universe  # Universe Builder
python3 -m unittest discover -s tests/universe -p 'test_*.py' -v  # Tests Universe
python3 -m brain_v2.test_integration  # Tests Brain v2
```

## Références Docs
- `/docs/YAGATI_KERNEL.md` : source de vérité
- `/docs/YAGATI_STATE.md` : snapshot actuel
- `/docs/YAGATI_DECISIONS.md` : journal décisions
- `/docs/YAGATI_CONTEXT_PACK.md` : ce fichier
- `/docs/OPS.md` : workflow équipe
- `/README.md` : vue d'ensemble
- `/docs/universe_builder.md` : Universe Builder détaillé
- `/brain_v2/README.md` : Brain v2 détaillé

---
**YAGATI Context Pack** — Bootstrap copiable pour nouveaux chats
