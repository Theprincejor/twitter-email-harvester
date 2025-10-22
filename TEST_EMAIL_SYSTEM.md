# Test Email System - How It Works

## Overview

The system now uses a **SINGLE list of test emails** for both warmup and checkpoint monitoring.

## How It Works

### 1. Test Email List
- **One CSV file** per campaign: `data/campaign_{campaign_id}_test_emails.csv`
- Contains all your monitoring/testing emails
- Format: `id,username,name,email`

### 2. Warmup Phase
When campaign starts with warmup enabled:
- **Uses first 10 emails** from test list
- Sends them sequentially with 10-minute intervals
- Example:
  ```
  email1@test.com  → Send → Wait 10 min
  email2@test.com  → Send → Wait 10 min
  email3@test.com  → Send → Wait 10 min
  ...
  email10@test.com → Send → Warmup complete!
  ```

### 3. Checkpoint Phase (During Campaign)
After warmup, during main campaign:
- **Rotates through ALL test emails** (including the first 10)
- Sends checkpoint email every N emails (default: 10)
- Continues rotating forever

Example with 20 test emails:
```
Campaign Email 10 → Checkpoint: email1@test.com
Campaign Email 20 → Checkpoint: email2@test.com
Campaign Email 30 → Checkpoint: email3@test.com
...
Campaign Email 200 → Checkpoint: email20@test.com
Campaign Email 210 → Checkpoint: email1@test.com (starts over)
Campaign Email 220 → Checkpoint: email2@test.com
```

## Benefits

✅ **Simpler**: One list instead of two
✅ **Complete rotation**: All test emails get checkpoint emails
✅ **No waste**: Warmup emails continue being used
✅ **Better monitoring**: Spread across all your test accounts

## Example Setup

### Your Test Emails (`data/campaign_azuki_test_emails.csv`):
```csv
id,username,name,email
1,test1,Test User 1,test1@gmail.com
2,test2,Test User 2,test2@gmail.com
3,test3,Test User 3,test3@gmail.com
4,test4,Test User 4,test4@gmail.com
5,test5,Test User 5,test5@gmail.com
6,test6,Test User 6,test6@gmail.com
7,test7,Test User 7,test7@gmail.com
8,test8,Test User 8,test8@gmail.com
9,test9,Test User 9,test9@gmail.com
10,test10,Test User 10,test10@gmail.com
11,monitor1,Monitor 1,monitor1@outlook.com
12,monitor2,Monitor 2,monitor2@yahoo.com
13,monitor3,Monitor 3,monitor3@gmail.com
```

### Campaign Flow:

**Warmup (if enabled):**
```
🔥 Warmup 1/10 → test1@gmail.com
   (wait 10 min)
🔥 Warmup 2/10 → test2@gmail.com
   (wait 10 min)
...
🔥 Warmup 10/10 → test10@gmail.com
✅ Warmup completed
```

**Main Campaign:**
```
📨 Sending 1/5000 → customer1@real.com
📨 Sending 2/5000 → customer2@real.com
...
📨 Sending 10/5000 → customer10@real.com
✓ Checkpoint 1 → test1@gmail.com (rotation index 0)

📨 Sending 11/5000 → customer11@real.com
...
📨 Sending 20/5000 → customer20@real.com
✓ Checkpoint 2 → test2@gmail.com (rotation index 1)

...

📨 Sending 130/5000 → customer130@real.com
✓ Checkpoint 13 → monitor1@outlook.com (rotation index 12)

...

📨 Sending 140/5000 → customer140@real.com
✓ Checkpoint 14 → test1@gmail.com (rotation starts over!)
```

## Adding Test Emails

### Via Telegram Bot:
```
📧 Add Emails
→ Select Campaign
→ Paste emails:
   test1@gmail.com, test2@gmail.com, test3@gmail.com
```

### Manually:
Edit `data/campaign_{campaign}_test_emails.csv`

## Migration from Old System

If you have old files:
- `templates/azuki_warmup.csv` → Automatically used as fallback
- `templates/azuki_checkpoint.csv` → No longer needed

System will automatically find and use old warmup files until you add new test emails.

## Configuration

In `config.yaml`:
```yaml
campaigns:
  azuki:
    # Remove these old settings:
    # warmup_emails: "templates/azuki_warmup.csv"
    # checkpoint_emails: "templates/azuki_checkpoint.csv"

    # No config needed! Test emails stored in data/ automatically
```

## FAQ

**Q: How many test emails should I have?**
A: 10-20 is good. More = better rotation coverage.

**Q: Can I use the same email multiple times?**
A: System automatically deduplicates, so no.

**Q: What if I have less than 10 test emails?**
A: Warmup will use however many you have (e.g., 5 emails = 5 warmup sends).

**Q: Can I add more test emails during a campaign?**
A: Yes! They'll be included in future checkpoint rotations.

**Q: Do warmup emails get used again?**
A: YES! That's the point. All test emails rotate forever.

## Summary

**Old System:**
- Separate warmup list (sent once)
- Separate checkpoint list (random selection)
- Wasted warmup emails

**New System:**
- One test email list
- First 10 = warmup (sent sequentially)
- All emails = checkpoint (full rotation)
- Nothing wasted!

🎯 **Result:** Simpler, more efficient, better monitoring!
