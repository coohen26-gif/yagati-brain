# YAGATI DECISIONS - Journal des Décisions

**Purpose**: Tracer les décisions architecturales et stratégiques importantes du projet YAGATI.

---

## 2026-01 - Janvier

### [2026-01-27] Context Pack Strategy
**Contexte**: Besoin d'externaliser le contexte de conversation pour éviter les discussions trop lourdes et améliorer la continuité du projet.

**Décision**: Implémentation de la stratégie "Context Pack"
- Création de 4 documents de référence dans `docs/`
- `YAGATI_KERNEL.md`: Source de vérité stable
- `YAGATI_STATE.md`: Snapshot court de l'état actuel (<120 lignes)
- `YAGATI_DECISIONS.md`: Ce fichier (journal de décisions)
- `YAGATI_CONTEXT_PACK.md`: Bootstrap copiable pour nouveaux chats (<120 lignes)

**Rationale**:
- Éviter les conversations GitHub trop lourdes
- Faciliter l'onboarding sur de nouvelles sessions
- Maintenir la continuité du contexte projet
- Réduire la répétition d'informations contextuelles

**Impact**: Documentation centralisée, meilleure collaboration

---

### [2026-01-26] Universe Builder Deployment
**Contexte**: Dépendance Supabase market-data peu fiable et non-déterministe.

**Décision**: Création du Universe Builder
- Module dédié: `brain_v2/universe/`
- APIs publiques: CoinGecko + Bitget
- Output déterministe: ≤50 symboles
- Tests complets: 31 tests unitaires/intégration

**Rationale**:
- Éliminer dépendance externe fragile (Supabase)
- Garantir déterminisme (mêmes entrées → mêmes sorties)
- Pas d'authentification requise (APIs publiques)
- Traçabilité complète (logging détaillé)

**Impact**: 
- ✅ Fiabilité accrue
- ✅ Reproductibilité garantie
- ✅ Indépendance vis-à-vis Supabase pour univers

**Documentation**: [docs/universe_builder.md](universe_builder.md)

---

### [2026-01-25] Brain v1 Quarantine
**Contexte**: Brain v1 présentait des violations de sécurité et architecture non-déterministe.

**Décision**: Quarantaine complète de Brain v1
- Déplacement vers `legacy_brain_v1/`
- Marqué OBSOLÈTE - NE PAS UTILISER
- Conservé uniquement pour audit
- Brain v2 devient la version PRODUCTION

**Rationale**:
- Violations de sécurité: Credentials en dur
- Architecture non-déterministe problématique
- Brain v2 offre toutes les fonctionnalités nécessaires
- Préserver historique pour audit

**Impact**:
- ✅ Amélioration sécurité
- ✅ Architecture déterministe (Brain v2)
- ❌ Brain v1 non-exécutable (intentionnel)

---

### [2026-01-20] Brain v2 Production Deployment
**Contexte**: Besoin d'un brain déterministe et auditable pour les décisions de trading.

**Décision**: Déploiement Brain v2 en production
- Architecture déterministe complète
- Intégration Airtable (brain_logs + setups_forming)
- Pas de credentials en dur
- Gouvernance & logging complets

**Rationale**:
- Décisions reproductibles et auditables
- Traçabilité complète des événements
- Sécurité renforcée (env vars uniquement)
- Meilleure maintenabilité

**Impact**:
- ✅ Brain v2 actif en production
- ✅ Logging Airtable opérationnel
- ✅ Détection setups fonctionnelle

**Documentation**: [brain_v2/README.md](../brain_v2/README.md)

---

### [2026-01-15] Operational Workflow Formalization
**Contexte**: Besoin de clarifier les rôles et processus de l'équipe.

**Décision**: Formalisation du workflow opérationnel
- ChatGPT décide de la direction
- Copilot implémente via PR
- GitHub = source de vérité
- confirmed = décision autoritaire
- Pas d'auto-optimisation
- SWING et DAY séparés

**Rationale**:
- Clarifier responsabilités
- Éviter modifications silencieuses
- Distinguer court-terme vs long-terme
- Améliorer review process

**Impact**:
- ✅ Process clair et documenté
- ✅ Meilleure collaboration
- ✅ Branches swing/* et day/* distinctes

**Documentation**: [docs/OPS.md](OPS.md)

---

## Principes de Décision

### Critères d'Évaluation
Toute décision importante doit être évaluée selon:
1. **Déterminisme**: La solution est-elle reproductible?
2. **Sécurité**: Y a-t-il des risques de sécurité?
3. **Maintenabilité**: Sera-t-elle facile à maintenir?
4. **Traçabilité**: Les actions sont-elles auditables?
5. **Impact**: Quel est l'impact sur l'existant?

### Process de Décision
1. Identification du problème/besoin
2. Proposition de solution(s)
3. Évaluation selon critères ci-dessus
4. Discussion et validation
5. Documentation dans ce journal
6. Implémentation via PR
7. Review et merge

---

## Format d'Entrée

### Template pour Nouvelle Décision
```markdown
### [YYYY-MM-DD] Titre de la Décision
**Contexte**: Description du problème ou besoin

**Décision**: Ce qui a été décidé
- Point 1
- Point 2
- Point 3

**Rationale**: Pourquoi cette décision
- Raison 1
- Raison 2

**Impact**:
- ✅ Impacts positifs
- ⚠️ Points d'attention
- ❌ Limitations connues

**Documentation**: Liens vers docs pertinentes
```

---

## Archive

Les décisions plus anciennes seront archivées ici si nécessaire pour maintenir ce fichier concis.

---

**Journal maintenu à jour**: Chaque décision importante doit être documentée ici.  
**Responsabilité**: Équipe projet (ChatGPT + Copilot)
