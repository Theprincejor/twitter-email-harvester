# Settings Feature - Implementation Plan

## Current Status
✅ Settings button shows current configuration
❌ Cannot change settings interactively

## What Settings Should Be Editable

### Per Campaign Settings:
1. **Daily Email Limit** (50/100/500/1000)
2. **Warmup Count** (how many warmup emails, default 10)
3. **Warmup Interval** (minutes between warmup, default 10)
4. **Checkpoint Interval** (every N emails, default 10)
5. **Enable/Disable Warmup & Checkpoint**

### Global Settings (in config.yaml):
- Delay per email (5 seconds default)
- Delay after batch (20 minutes default)
- Max retries (3 default)

## Implementation Approach

### Option 1: During Campaign Start (Current)
✅ Already implemented
- User selects warmup yes/no when starting campaign
- User selects daily limit (50/100/500/1000)
- These are saved per campaign run

### Option 2: Dedicated Settings Menu (To Add)
Would allow:
```
⚙️ Settings
→ Select Campaign
→ Change Daily Limit
→ Change Warmup Count
→ Change Checkpoint Interval
→ Toggle Warmup/Checkpoint On/Off
```

## Quick Solution (For Now)

The current approach works well:
1. Settings are configured when **starting a campaign**
2. Each campaign run can have different settings
3. Previous settings are saved in state

## Full Interactive Settings (Future Enhancement)

Would need:
```python
# New conversation states
WAITING_SETTINGS_CAMPAIGN
WAITING_SETTINGS_CHOICE
WAITING_SETTINGS_VALUE

# New handlers
async def settings_menu():
    # Show campaigns to configure

async def edit_daily_limit():
    # Change mails per day

async def edit_warmup_settings():
    # Change warmup count/interval

async def edit_checkpoint_interval():
    # Change checkpoint frequency
```

## Recommendation

**Current system is sufficient** because:
1. ✅ You can set everything when starting campaign
2. ✅ Different runs can have different settings
3. ✅ Settings are persisted in campaign state
4. ✅ View settings shows current configuration

**If you want interactive settings editing, let me know and I'll implement it!**

For now, to change settings:
1. Start a new campaign
2. Choose your settings during setup
3. Those settings apply to that campaign run
