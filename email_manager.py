"""
Email List Manager - Manage warmup and checkpoint emails
"""
import csv
import os
from typing import List, Dict


class EmailListManager:
    """Manage warmup and checkpoint email lists"""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)

    def parse_email_input(self, email_text: str) -> List[Dict[str, str]]:
        """
        Parse email input from various formats:
        - Comma-separated: email1@test.com, email2@test.com
        - Line-separated: one email per line
        - With names: Name1 <email1@test.com>, Name2 <email2@test.com>
        """
        emails = []

        # Split by comma or newline
        if ',' in email_text:
            parts = email_text.split(',')
        else:
            parts = email_text.split('\n')

        for idx, part in enumerate(parts, start=1):
            part = part.strip()
            if not part:
                continue

            # Check if format is: Name <email>
            if '<' in part and '>' in part:
                name = part.split('<')[0].strip()
                email = part.split('<')[1].split('>')[0].strip()
            elif '@' in part:
                email = part
                name = email.split('@')[0]
            else:
                continue

            emails.append({
                'id': str(idx),
                'username': name.replace(' ', '_').lower(),
                'name': name,
                'email': email
            })

        return emails

    def add_test_emails(self, campaign_id: str, email_text: str) -> Dict:
        """Add test emails to campaign (used for both warmup and checkpoint rotation)"""
        # Store in data directory for better organization
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, f"campaign_{campaign_id}_test_emails.csv")

        # Parse emails
        new_emails = self.parse_email_input(email_text)

        if not new_emails:
            return {"success": False, "message": "No valid emails found"}

        # Load existing emails
        existing_emails = []
        existing_set = set()

        if os.path.exists(filepath):
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_emails.append(row)
                    existing_set.add(row['email'].lower())

        # Add new emails (skip duplicates)
        added_count = 0
        next_id = len(existing_emails) + 1

        for email_data in new_emails:
            if email_data['email'].lower() not in existing_set:
                email_data['id'] = str(next_id)
                existing_emails.append(email_data)
                existing_set.add(email_data['email'].lower())
                added_count += 1
                next_id += 1

        # Write back to file
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'username', 'name', 'email']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_emails)

        return {
            "success": True,
            "message": f"Added {added_count} test emails (skipped {len(new_emails) - added_count} duplicates)",
            "total": len(existing_emails)
        }

    def add_warmup_emails(self, campaign_id: str, email_text: str) -> Dict:
        """Alias for add_test_emails (backwards compatibility)"""
        return self.add_test_emails(campaign_id, email_text)

    def add_checkpoint_emails(self, campaign_id: str, email_text: str) -> Dict:
        """Add checkpoint emails to campaign"""
        filepath = os.path.join(self.templates_dir, f"{campaign_id}_checkpoint.csv")

        # Parse emails
        new_emails = self.parse_email_input(email_text)

        if not new_emails:
            return {"success": False, "message": "No valid emails found"}

        # Load existing emails
        existing_emails = []
        existing_set = set()

        if os.path.exists(filepath):
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_emails.append(row)
                    existing_set.add(row['email'].lower())

        # Add new emails (skip duplicates)
        added_count = 0
        next_id = len(existing_emails) + 1

        for email_data in new_emails:
            if email_data['email'].lower() not in existing_set:
                email_data['id'] = str(next_id)
                existing_emails.append(email_data)
                existing_set.add(email_data['email'].lower())
                added_count += 1
                next_id += 1

        # Write back to file
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'username', 'name', 'email']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_emails)

        return {
            "success": True,
            "message": f"Added {added_count} checkpoint emails (skipped {len(new_emails) - added_count} duplicates)",
            "total": len(existing_emails)
        }

    def list_test_emails(self, campaign_id: str) -> List[Dict]:
        """List all test emails for a campaign"""
        # Try new location first
        data_dir = "data"
        filepath = os.path.join(data_dir, f"campaign_{campaign_id}_test_emails.csv")

        # Fallback to old warmup location
        if not os.path.exists(filepath):
            filepath = os.path.join(self.templates_dir, f"{campaign_id}_warmup.csv")

        if not os.path.exists(filepath):
            return []

        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def list_warmup_emails(self, campaign_id: str) -> List[Dict]:
        """Alias for list_test_emails (backwards compatibility)"""
        return self.list_test_emails(campaign_id)

    def list_checkpoint_emails(self, campaign_id: str) -> List[Dict]:
        """List all checkpoint emails for a campaign"""
        filepath = os.path.join(self.templates_dir, f"{campaign_id}_checkpoint.csv")

        if not os.path.exists(filepath):
            return []

        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def clear_warmup_emails(self, campaign_id: str) -> Dict:
        """Clear all warmup emails for a campaign"""
        filepath = os.path.join(self.templates_dir, f"{campaign_id}_warmup.csv")

        if not os.path.exists(filepath):
            return {"success": False, "message": "No warmup emails found"}

        os.remove(filepath)
        return {"success": True, "message": "Warmup emails cleared"}

    def clear_checkpoint_emails(self, campaign_id: str) -> Dict:
        """Clear all checkpoint emails for a campaign"""
        filepath = os.path.join(self.templates_dir, f"{campaign_id}_checkpoint.csv")

        if not os.path.exists(filepath):
            return {"success": False, "message": "No checkpoint emails found"}

        os.remove(filepath)
        return {"success": True, "message": "Checkpoint emails cleared"}

    def remove_email(self, campaign_id: str, email_type: str, email_address: str) -> Dict:
        """Remove a specific email from warmup or checkpoint list"""
        if email_type not in ['warmup', 'checkpoint']:
            return {"success": False, "message": "Invalid email type"}

        filepath = os.path.join(self.templates_dir, f"{campaign_id}_{email_type}.csv")

        if not os.path.exists(filepath):
            return {"success": False, "message": f"No {email_type} emails found"}

        # Read existing emails
        emails = []
        found = False

        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].lower() != email_address.lower():
                    emails.append(row)
                else:
                    found = True

        if not found:
            return {"success": False, "message": "Email not found"}

        # Write back
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'username', 'name', 'email']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(emails)

        return {
            "success": True,
            "message": f"Removed {email_address} from {email_type} list",
            "remaining": len(emails)
        }
