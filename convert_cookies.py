import json


def convert_cookies(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    cookie_dict = {}
    for c in cookies:
        # Only keep name → value mapping
        cookie_dict[c["name"]] = c["value"]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cookie_dict, f, indent=4)


# Example: run for both accounts
convert_cookies("account1_browser_cookies.json", "account1_twitter_cookies.json")
convert_cookies("account2_browser_cookies.json", "account2_twitter_cookies.json")
convert_cookies("account3_browser_cookies.json", "account3_twitter_cookies.json")
