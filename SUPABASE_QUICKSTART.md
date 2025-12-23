# Supabase Integration - Quick Start Guide

## What Was Added

✅ Automatic round data storage to Supabase
✅ Works even if database connection fails (graceful degradation)
✅ Zero configuration - just run `python main.py`

## Installation

The Supabase client is automatically installed when you run:

```bash
pip install supabase
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

## Running the App

No changes to how you use the app:

```bash
python main.py
```

## What Happens

### On Startup
```
[15:23:45] INFO: Supabase connected successfully
[15:23:45] INFO: Started
```

### When a Round Completes
```
[15:25:30] [CRASH] Reached 8.75x in 7.12s

[ROUND ENDED]
Round 1 completed...

[15:25:30] INFO: Round 1 saved to Supabase (multiplier: 8.75x)
```

### On Exit
```
[15:30:00] INFO: Supabase inserts: 5
[15:30:00] INFO: Supabase failures: 0
```

## Viewing Your Data

Open Supabase dashboard:
https://supabase.com/dashboard/project/zofojiubrykbtmstfhzx

Go to: Table Editor → AviatorRound

You'll see all your round data with:
- **roundid** (1, 2, 3...)
- **multiplier** (e.g., 8.75)
- **timestamp** (e.g., 2025-12-23 15:25:46)

## If Supabase Connection Fails

The app will show:

```
[15:23:45] WARNING: Supabase connection failed: ...
[15:23:45] INFO: Continuing with local logging only
```

**This is OK!** The app continues working normally:
- Multipliers read from screen
- Rounds tracked locally
- Just not saved to database

When connection recovers, new rounds will save automatically.

## Disable Supabase

To turn off Supabase integration, edit main.py line 60:

```python
# Replace this:
self.supabase = SupabaseLogger(url='...', key='...')

# With this:
self.supabase = SupabaseLogger()  # Disabled
```

Then save and run. App will work with local logging only.

## Troubleshooting

### No data appearing in Supabase

1. Check dashboard: https://supabase.com/dashboard/project/zofojiubrykbtmstfhzx
2. Go to: Table Editor → AviatorRound
3. If table is empty, wait for next round completion
4. If still empty after 1 round, check terminal output for errors

### Getting "Failed to save round to Supabase"

This means the insert failed but app continues working. Possible causes:
- Internet disconnected
- Supabase service down
- RLS policy issue

**Solution**: Wait for connection to recover. New rounds will save when connection is back.

### Want to store more data

You can expand the table to include:
- Round start time
- Round duration
- Event count
- Crash status

See SUPABASE_INTEGRATION.md for how to do this.

## Files Added/Modified

**New:**
- `supabase_client.py` - Supabase connection handler
- `SUPABASE_INTEGRATION.md` - Full documentation
- `SUPABASE_QUICKSTART.md` - This file

**Modified:**
- `requirements.txt` - Added supabase>=2.0.0
- `main.py` - Added Supabase initialization and insert calls

## That's It!

Just run `python main.py` and your round data will automatically save to Supabase.

For detailed information, see:
- **SUPABASE_INTEGRATION.md** - Complete documentation
- **supabase_client.py** - Implementation code

---

Questions? Check SUPABASE_INTEGRATION.md Troubleshooting section.
