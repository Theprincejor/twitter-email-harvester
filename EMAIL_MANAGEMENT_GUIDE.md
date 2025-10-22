# Email Management Guide

This guide explains how to manage warmup and checkpoint emails via Telegram bot.

## Overview

You can now add, view, and manage warmup/checkpoint emails directly from Telegram without editing CSV files manually!

## Commands

### `/add_emails` - Add Warmup/Checkpoint Emails

Add emails in bulk using flexible formats:

**Step 1:** Send `/add_emails`

**Step 2:** Select campaign (e.g., "Azuki Campaign")

**Step 3:** Select type:
- 🔥 Warmup Emails - Sent before campaign starts
- ✓ Checkpoint Emails - Sent periodically during campaign

**Step 4:** Send emails in any of these formats:

#### Format 1: Comma-Separated
```
email1@test.com, email2@test.com, email3@test.com
```

#### Format 2: Line-Separated
```
email1@test.com
email2@test.com
email3@test.com
```

#### Format 3: With Names
```
John Doe <john@test.com>, Jane Smith <jane@test.com>
```

#### Format 4: Mixed
```
John <john@test.com>,
jane@test.com,
Bob Smith <bob@test.com>
```

**Example:**
```
User: /add_emails
Bot: Select campaign → [Azuki Campaign]
User: [Select Azuki]
Bot: Select type → [Warmup] or [Checkpoint]
User: [Select Warmup]
Bot: Send emails...
User: john@gmail.com, jane@gmail.com, bob@gmail.com
Bot: ✅ Added 3 warmup emails (skipped 0 duplicates)
     📊 Total warmup emails: 13
```

### `/view_emails` - View Current Email Lists

View all warmup or checkpoint emails for a campaign.

**Example:**
```
User: /view_emails
Bot: Select campaign → [Azuki Campaign]
User: [Select Azuki]
Bot: Select type → [Warmup] or [Checkpoint]
User: [Select Warmup]
Bot: 📧 Warmup Emails (13 total)

     1. john@gmail.com (john)
     2. jane@gmail.com (jane)
     3. bob@gmail.com (bob)
     ...
```

### `/clear_emails` - Clear Email Lists (Coming Soon)

Will allow clearing all emails from warmup or checkpoint lists.

## Benefits

### 1. Easy Bulk Upload
Add hundreds of emails at once:
```
email1@test.com, email2@test.com, email3@test.com, ...
```

### 2. Duplicate Prevention
The system automatically skips duplicate emails:
```
✅ Added 5 warmup emails (skipped 2 duplicates)
```

### 3. Multiple Formats
Send emails however you want - the bot parses them all:
- Copy-paste from spreadsheet
- Comma-separated list
- One per line
- With or without names

### 4. No File Editing
No need to manually edit CSV files or SSH into server.

### 5. Real-Time Updates
Changes take effect immediately for new campaigns.

## Use Cases

### Adding Personal Email Accounts for Warmup
```
/add_emails
→ Azuki Campaign
→ Warmup Emails
→ myemail1@gmail.com, myemail2@gmail.com, myemail3@gmail.com
```

### Adding Monitoring Emails for Checkpoints
```
/add_emails
→ Azuki Campaign
→ Checkpoint Emails
→ monitor@gmail.com, check@gmail.com
```

### Bulk Import from List
Copy your list and paste:
```
john.doe@company.com
jane.smith@company.com
bob.wilson@company.com
alice.johnson@company.com
charlie.brown@company.com
```

## Technical Details

### Storage
Emails are stored in CSV files:
- `templates/[campaign]_warmup.csv`
- `templates/[campaign]_checkpoint.csv`

### Format
CSV structure:
```csv
id,username,name,email
1,john,John Doe,john@test.com
2,jane,Jane Smith,jane@test.com
```

### Parsing Logic
The bot extracts emails using these rules:
1. Split by comma or newline
2. Check for `Name <email>` format
3. Extract email address with `@`
4. Generate username from name or email
5. Auto-increment ID

### Duplicate Detection
- Case-insensitive email comparison
- Existing emails are not duplicated
- Count of skipped duplicates is reported

## Best Practices

### Warmup Emails
- Use 10-20 personal email accounts
- These should be emails you control
- They receive test campaigns first
- Helps establish sender reputation

**Good warmup emails:**
- Your personal Gmail accounts
- Team member emails
- Test accounts you own

### Checkpoint Emails
- Use 2-5 monitoring addresses
- These check if emails reach inbox
- Sent every N emails (e.g., every 10)
- Monitor for spam placement

**Good checkpoint emails:**
- Gmail account (checks Gmail delivery)
- Outlook account (checks Microsoft delivery)
- Custom domain (checks business email delivery)

### Adding Many Emails
For bulk operations:
1. Prepare list in text editor
2. Format as comma-separated or line-separated
3. Copy entire list
4. Paste into Telegram
5. Bot processes all at once

**Limit:** No hard limit, but Telegram messages max ~4000 characters
- ~400 emails per message (if email@test.com format)
- Send multiple messages if needed

## Troubleshooting

### "No valid emails found"
- Make sure emails contain `@` symbol
- Check format: `user@domain.com`
- Remove extra spaces

### Duplicate emails not added
- This is normal behavior
- Duplicates are automatically skipped
- Check `/view_emails` to see existing list

### Changes not taking effect
- Changes apply to NEW campaigns
- Stop and restart campaign to reload
- Or start a new campaign

## Advanced Usage

### Adding with Custom Names
```
Marketing Team <marketing@company.com>,
Support Team <support@company.com>,
Sales Team <sales@company.com>
```

### Importing from Spreadsheet
1. Copy column from Excel/Google Sheets
2. Paste into Telegram
3. Bot auto-detects line breaks

### Testing Email Lists
After adding emails, test the campaign:
1. Set mails per day to 10
2. Enable warmup/checkpoint
3. Monitor delivery
4. Adjust list as needed

## Examples

### Complete Workflow: Setting Up Campaign

```
# Step 1: Add warmup emails
/add_emails
→ Azuki Campaign
→ Warmup Emails
→ warmup1@gmail.com, warmup2@gmail.com, warmup3@gmail.com

# Step 2: Add checkpoint emails
/add_emails
→ Azuki Campaign
→ Checkpoint Emails
→ check1@gmail.com, check2@outlook.com

# Step 3: Verify emails
/view_emails
→ Azuki Campaign
→ Warmup Emails
(Shows 3 emails)

# Step 4: Start campaign
/start_process
→ azuki (Twitter username)
→ Azuki Campaign
→ Use warmup? Yes
→ Emails per day? 100
→ Confirm & Start
```

## FAQ

**Q: Can I add emails while campaign is running?**
A: Yes, but they'll only be used for new campaigns. Restart campaign to use new emails.

**Q: How many emails can I add at once?**
A: As many as fit in a Telegram message (~400 emails). Send multiple messages for more.

**Q: Can I remove specific emails?**
A: Currently no, but you can manually edit CSV files or clear and re-add all emails.

**Q: Do I need to add warmup emails?**
A: No, warmup is optional. But recommended for new domains/IPs.

**Q: What if I don't have checkpoint emails?**
A: You can disable checkpoint feature when starting campaign (select "No" for warmup/checkpoint).

**Q: Can different campaigns use same emails?**
A: Yes, each campaign has separate warmup/checkpoint lists.

## Summary

Email management via Telegram makes it easy to:
- ✅ Add emails in bulk
- ✅ Support multiple formats
- ✅ Prevent duplicates
- ✅ View current lists
- ✅ No manual file editing
- ✅ Real-time updates

Just use `/add_emails` and paste your list! 🚀
