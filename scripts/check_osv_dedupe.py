"""OSV 중복 제거 후 '등급 없는 취약점'이 몇 건 남는지 확인. check_apis.py와 같은 폴더에서 실행."""
import json
import pathlib

for f in sorted(pathlib.Path("tests/fixtures").glob("osv_*.json")):
    vulns = json.loads(f.read_text(encoding="utf-8")).get("vulns", [])
    groups = []  # 같은 취약점(id·aliases가 겹침)끼리 묶기
    for v in vulns:
        ids = {v["id"], *v.get("aliases", [])}
        sev = (v.get("database_specific") or {}).get("severity")
        for g in groups:
            if g["ids"] & ids:
                g["ids"] |= ids
                g["sev"] = g["sev"] or sev
                break
        else:
            groups.append({"ids": ids, "sev": sev})
    no_sev = [sorted(g["ids"])[0] for g in groups if not g["sev"]]
    levels = sorted({g["sev"] for g in groups if g["sev"]})
    print(f"{f.stem}: 원래 {len(vulns)}건 → 묶은 뒤 {len(groups)}건, 등급 없음 {len(no_sev)}건, 등급 종류 {levels}")
    if no_sev:
        print("   등급 없는 예:", no_sev[:3])
