"""手動実行で指定したPayPay URLだけを、公開設定ファイルへ保存する。"""
import base64
from datetime import datetime, timezone
import json
import os
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def validate_url(value):
    value = value.strip()
    parsed = urlsplit(value)
    if (len(value) > 2048 or re.search(r"\s", value)
            or parsed.scheme != "https" or parsed.netloc != "qr.paypay.ne.jp"
            or parsed.fragment or not re.fullmatch(r"/p2p01_[A-Za-z0-9_-]{8,200}", parsed.path)):
        raise ValueError("PayPayの送金リンクを入力してください。")
    return value


def update(url, token):
    endpoint = "https://api.github.com/repos/skikkh/skikkh.github.io/contents/links/paypay.json"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "paypay-link-updater"}
    with urlopen(Request(endpoint + "?ref=main", headers=headers), timeout=20) as response:
        previous = json.load(response)
    content = json.dumps({"url": url, "updatedAt": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n"
    payload = json.dumps({"message": "Update PayPay link", "branch": "main", "sha": previous["sha"],
                          "content": base64.b64encode(content.encode()).decode()}).encode()
    with urlopen(Request(endpoint, data=payload, headers=headers, method="PUT"), timeout=20) as response:
        return json.load(response)["commit"]["sha"]


if __name__ == "__main__":
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise SystemExit("mainブランチを選んで実行してください。")
    url = validate_url(os.environ["PAYPAY_URL"])
    sha = update(url, os.environ["GH_TOKEN"])
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise SystemExit("更新結果のコミットを確認できませんでした。")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"commit_sha={sha}\n")
    print("PayPayリンクを更新しました。続いてサイトへ反映します。")
