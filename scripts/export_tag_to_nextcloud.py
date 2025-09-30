#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Paperless → Nextcloud Export Script
===================================

This script exports documents from Paperless-ngx into Nextcloud via WebDAV.

Features:
- Iterates over Paperless documents using its REST API.
- Matches rules defined in `routing.json` (tags, correspondents, type, title).
- Creates remote directories in Nextcloud (MKCOL).
- Uploads documents with configurable filename templates.
- Supports overwrite vs append behavior.
- Designed for both generic Docker/Linux hosts and Unraid setups.

Requirements:
- Paperless-ngx with API enabled
- Tika and Gotenberg containers running for Paperless
- Nextcloud instance with WebDAV enabled (`remote.php/dav/files/<username>/`)

Environment variables (via `.env`):
- PAPERLESS_URL
- PAPERLESS_TOKEN
- BASE_NC_URL
- NC_USER
- NC_PASS

Usage:
    python3 export_tag_to_nextcloud.py \
        --paperless "$PAPERLESS_URL" \
        --token "$PAPERLESS_TOKEN" \
        --base-nc-url "$BASE_NC_URL" \
        --nc-user "$NC_USER" \
        --nc-pass "$NC_PASS" \
        --routing /path/to/routing.json

Author: CHEYNOLDS  (https://github.com/cheynolds)
License: MIT
"""






import argparse, base64, json, os, ssl, urllib.parse, urllib.request, pathlib

def http(method, url, headers=None, data=None, insecure=False, ok=(200,201,204,207)):
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    ctx = ssl._create_unverified_context() if insecure else None
    with urllib.request.urlopen(req, context=ctx) as resp:
        if resp.status not in ok:
            raise RuntimeError(f"HTTP {resp.status} {url}")
        return resp.read()

def iter_paginated(url, headers, insecure=False):
    while url:
        obj = json.loads(http("GET", url, headers=headers, insecure=insecure).decode())
        for item in obj.get("results", []):
            yield item
        url = obj.get("next")

def sanitize(s):
    if s is None:
        s = ""
    for ch in '/\\:*?"<>|':
        s = s.replace(ch, "-")
    return " ".join(s.split()).strip()

def mkcol_recursive(base_url, rel_path, auth, insecure):
    parts = [p for p in rel_path.strip("/").split("/") if p]
    cur = base_url.rstrip("/")
    for p in parts:
        cur = cur + "/" + urllib.parse.quote(p)
        print("MKCOL →", cur + "/")   # debug log
        try:
            http("MKCOL", cur + "/", headers={"Authorization": auth}, insecure=insecure)
        except Exception as e:
            print("  MKCOL skipped/error:", e)  # already exists or error

def matches(rule_if, doc, tag_names):
    """Support: tags_any, tags_all, correspondent (id or name), type (id or name),
    title_contains (case-insensitive)."""
    if not rule_if:
        return True

    if "tags_any" in rule_if:
        wanted = set(t.lower() for t in rule_if["tags_any"])
        if wanted.isdisjoint(set(t.lower() for t in tag_names)):
            return False

    if "tags_all" in rule_if:
        wanted = set(t.lower() for t in rule_if["tags_all"])
        have = set(t.lower() for t in tag_names)
        if not wanted.issubset(have):
            return False

    if "correspondent" in rule_if:
        rule_corr = str(rule_if["correspondent"]).lower()
        doc_corr_name = str(doc.get("correspondent__name") or "").lower()
        doc_corr_id = str(doc.get("correspondent") or "").lower()
        if rule_corr not in (doc_corr_name, doc_corr_id):
            return False

    if "type" in rule_if:
        rule_type = str(rule_if["type"]).lower()
        doc_type_name = str(doc.get("document_type__name") or "").lower()
        doc_type_id = str(doc.get("document_type") or "").lower()
        if rule_type not in (doc_type_name, doc_type_id):
            return False

    if "title_contains" in rule_if:
        if str(rule_if["title_contains"]).lower() not in str(doc.get("title") or "").lower():
            return False

    return True

def fill_path(path_tpl, doc):
    created = (doc.get("created") or "")[:10] or "0000-00-00"
    year = created[:4]
    return (path_tpl
            .replace("{year}", year)
            .replace("{correspondent}", sanitize(doc.get("correspondent__name") or "Unfiled"))
            .replace("{type}", sanitize(doc.get("document_type__name") or "Unfiled")))

def render_filename(tpl, doc):
    created = (doc.get("created") or "")[:10] or "0000-00-00"
    title = sanitize(doc.get("title") or f"document-{doc['id']}")
    name = tpl.replace("{created}", created).replace("{title}", title)\
              .replace("{correspondent}", sanitize(doc.get("correspondent__name") or ""))\
              .replace("{type}", sanitize(doc.get("document_type__name") or ""))
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name

def main():
    ap = argparse.ArgumentParser(description="Route Paperless docs to Nextcloud via routing.json")
    ap.add_argument("--paperless", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--base-nc-url", dest="base_nc_url", required=True,
                    help="https://.../remote.php/dav/files/<user>/")
    ap.add_argument("--nc-user", dest="nc_user", required=True)
    ap.add_argument("--nc-pass", dest="nc_pass", required=True)
    ap.add_argument("--routing", default="/state/routing.json")
    ap.add_argument("--state-dir", default="/state")
    ap.add_argument("--insecure", action="store_true")
    args = ap.parse_args()

    routing = json.load(open(args.routing, "r"))
    rules = routing.get("rules", [])
    filename_tpl = routing.get("filename_template", "{created} - {title}.pdf")
    overwrite = bool(routing.get("upload", {}).get("overwrite", True))
    original = bool(routing.get("upload", {}).get("original", False))

    pl_h = {"Authorization": f"Token {args.token}"}
    nc_auth = "Basic " + base64.b64encode(f"{args.nc_user}:{args.nc_pass}".encode()).decode()
    pathlib.Path(args.state_dir).mkdir(parents=True, exist_ok=True)

    tag_map = {t["id"]: t["name"] for t in iter_paginated(
        urllib.parse.urljoin(args.paperless, "/api/tags/?page_size=1000"), pl_h, args.insecure)}

    docs_url = urllib.parse.urljoin(args.paperless, "/api/documents/?page_size=100")
    state_cache = {}
    exported_total = 0

    for doc in iter_paginated(docs_url, pl_h, args.insecure):
        tag_names = [tag_map.get(t, "") for t in doc.get("tags", [])]
        dests = []

        for rule in rules:
            if rule.get("default"):
                default_path = rule["to"]
                continue
            cond = rule.get("if", {})
            if matches(cond, doc, tag_names):
                dests.append(rule["to"])

        if not dests:
            default_rule = next((r for r in rules if r.get("default")), None)
            if default_rule:
                dests = [default_rule["to"]]
            else:
                continue

        dl = urllib.parse.urljoin(
            args.paperless,
            f"/api/documents/{doc['id']}/download/?original={'true' if original else 'false'}"
        )
        blob = http("GET", dl, headers=pl_h, insecure=args.insecure)
        filename = render_filename(filename_tpl, doc)

        for dest in dests:
            subpath = fill_path(dest, doc).strip("/")
            state_path = os.path.join(args.state_dir, f"{subpath.replace('/','_')}.ids")
            if state_path not in state_cache:
                state_cache[state_path] = set(open(state_path).read().split()) if os.path.exists(state_path) else set()
            doc_id = str(doc["id"])
            if doc_id in state_cache[state_path]:
                continue

            mkcol_recursive(args.base_nc_url, subpath, nc_auth, args.insecure)

            put_url = args.base_nc_url.rstrip("/") + "/" + "/".join(
                [urllib.parse.quote(p) for p in subpath.split("/") if p] + [urllib.parse.quote(filename)]
            )

            do_put = True
            if not overwrite:
                try:
                    http("HEAD", put_url, headers={"Authorization": nc_auth}, insecure=args.insecure)
                    print(f"SKIP (exists, overwrite disabled) → {put_url}")
                    do_put = False
                except RuntimeError:
                    do_put = True

            if do_put:
                print("PUT →", put_url)  # debug log
                http("PUT", put_url,
                     headers={"Authorization": nc_auth, "Content-Type": "application/pdf"},
                     data=blob, insecure=args.insecure)
                with open(state_path, "a") as f:
                    f.write(doc_id + "\n")
                state_cache[state_path].add(doc_id)
                exported_total += 1
                print(f"Exported {doc_id} → {subpath}/{filename}")

    print(f"Done. New exports: {exported_total}")

if __name__ == "__main__":
    main()
