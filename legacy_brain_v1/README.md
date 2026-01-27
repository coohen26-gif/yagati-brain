# ⚠️ LEGACY — Brain v1 (OBSOLETE)

**Status**: QUARANTINED - DO NOT USE

This directory contains the deprecated Brain v1 implementation.
It is kept for audit purposes and historical reference only.

## ⚠️ Critical Warnings

❌ **DO NOT** use in production  
❌ **DO NOT** modify this code  
❌ **DO NOT** import from this directory  

## ✅ Migration Path

✅ **Use `brain_v2/` instead** - The active, production-ready implementation

## Why This Was Quarantined

- Brain v1 contained hardcoded Supabase credentials (security violation)
- Architecture was event-driven and not fully deterministic
- Brain v2 provides a clean, deterministic, auditable implementation
- Keeping v1 active created confusion about which system was canonical

## Removal Timeline

This directory will be permanently removed after Brain v2 has been validated in production for at least 30 days.

**Expected removal date**: TBD (after Brain v2 validation)

## For Historical Reference

- Original entry point: `brain_loop.py`
- Scanner version: v1.1.3-01
- Last active: 2026-01-27 (before quarantine)
