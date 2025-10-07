# validator.py
from lxml import etree
from collections import Counter
from pathlib import Path
import json, sys
from rich import print
from jinja2 import Template

def load_xml(path: Path):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(path), parser)

def find_text(node, tag):
    el = node.find(f".//{tag}")
    return el.text if el is not None and el.text is not None else None

def xpath_text(root, xp):
    els = root.xpath(xp)
    out = []
    for e in els:
        txt = e.text if isinstance(e, etree._Element) else str(e)
        out.append(txt)
    return out

def rule_duplicate_short_names(tree, root):
    shorts = root.xpath(".//SHORT-NAME")
    names = [s.text for s in shorts if s.text]
    dupes = [n for n, c in Counter(names).items() if c > 1]
    issues = []
    for n in dupes:
        for el in root.xpath(f".//*[SHORT-NAME='{n}']"):
            issues.append({
                "rule": "DUP_SHORT_NAME",
                "message": f"Duplicate SHORT-NAME '{n}'",
                "xpath": tree.getpath(el)
            })
    return issues

def rule_missing_type_ref(tree, root):
    issues = []
    for vdp in root.xpath(".//VARIABLE-DATA-PROTOTYPE"):
        has_tref = vdp.find(".//TYPE-TREF") is not None
        if not has_tref:
            name = find_text(vdp, "SHORT-NAME") or "<unnamed>"
            issues.append({
                "rule": "NO_TYPE_TREF",
                "message": f"VARIABLE-DATA-PROTOTYPE '{name}' missing TYPE-TREF",
                "xpath": tree.getpath(vdp)
            })
    return issues

def rule_compu_without_unit_or_range(tree, root):
    issues = []
    for cm in root.xpath(".//COMPU-METHOD"):
        name = find_text(cm, "SHORT-NAME") or "<unnamed>"
        unit_ref = cm.find(".//UNIT-REF")
        has_scale = cm.find(".//COMPU-SCALE") is not None
        if unit_ref is None or not has_scale:
            issues.append({
                "rule": "COMPU_METHOD_INCOMPLETE",
                "message": f"COMPU-METHOD '{name}' missing UNIT-REF or COMPU-SCALE",
                "xpath": tree.getpath(cm)
            })
    return issues

def generate_html(issues, out_html):
    tmpl = Template("""
    <html><head><meta charset="utf-8"><title>ARXML Validation Report</title>
    <style>body{font-family:system-ui;margin:20px}
    table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}
    th{background:#f2f2f2}</style></head><body>
    <h2>ARXML Validation Report</h2>
    <p>Total issues: {{ issues|length }}</p>
    <table>
      <tr><th>#</th><th>Rule</th><th>Message</th><th>XPath</th></tr>
        {% for iss in issues %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ iss.rule }}</td>
                <td>{{ iss.message }}</td>
                <td><code>{{ iss.xpath }}</code></td>
            </tr>
        {% endfor %}
    </table>
    </body></html>
    """)
    Path(out_html).write_text(tmpl.render(issues=issues), encoding="utf-8")

def main():
    import webbrowser
    import sys
    from pathlib import Path

    #1️. basic CLI check
    if len(sys.argv) < 3:
        print("[yellow]Usage:[/yellow] python validator.py <input_file_or_dir> <output_dir>")
        sys.exit(1)

    # 2️. create paths early
    in_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    #3. validation logic (your existing code here)
    tree = load_xml(in_path)
    root = tree.getroot()

    issues = []
    issues += rule_duplicate_short_names(tree, root)
    issues += rule_missing_type_ref(tree, root)
    issues += rule_compu_without_unit_or_range(tree, root)

    # write report files
    generate_html(issues, out_dir / "index.html")

    #safe browser open
    html_file = out_dir / "index.html"
    if html_file.exists():
        try:
            webbrowser.open(str(html_file.resolve()))
        except Exception as e:
            print(f"[red]Could not open browser automatically:[/red] {e}")

    print(f"[green]Validated:[/green] {in_path}")
    print(f"[cyan]Issues:[/cyan] {len(issues)} → reports in {out_dir}")
    

if __name__ == "__main__":
    main()