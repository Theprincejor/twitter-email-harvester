import csv
from datetime import datetime


def export_to_csv(results, target):
    filename = f"emails_{target}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["screen_name", "profile_url", "profile_emails", "site_emails"])
        for r in results:
            writer.writerow(
                [
                    r["screen_name"],
                    r.get("profile_url") or "",
                    ";".join(r["profile_emails"]),
                    ";".join(r["site_emails"]),
                ]
            )
    return filename
