import os
import re

def fix_analytics_dir():
    file_path = "src/analytics.py"
    with open(file_path, "r") as f:
        content = f.read()

    new_content = content.replace(
        'conn = sqlite3.connect("data/analytics.db")',
        'os.makedirs("data", exist_ok=True)\n        conn = sqlite3.connect("data/analytics.db")'
    )
    with open(file_path, "w") as f:
        f.write(new_content)

def fix_dashboard():
    file_path = "src/dashboard.py"
    with open(file_path, "r") as f:
        content = f.read()

    # Add html escape
    if "import html" not in content:
        content = "import html\n" + content

    # Replace inventory loading
    content = content.replace(
        "item['product_name']", "html.escape(str(item['product_name']))"
    )
    content = content.replace(
        "item['price_usd']", "html.escape(str(item['price_usd']))"
    )

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_analytics_dir()
    fix_dashboard()
