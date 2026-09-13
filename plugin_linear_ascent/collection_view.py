"""Pixel collection presentation. Actions and numbers come from the engine."""
from html import escape

COLORS = {"Common": "#aab8b4", "Rare": "#69aee8", "Epic": "#bd8feb", "Legendary": "#ebbd61"}


def render(data: dict, art_url, icon) -> str:
    e = lambda x: escape(str(x), quote=True)
    items = {i["id"]: i for i in data["items"]}
    slots = []
    for n, iid in enumerate(data["deck"], 1):
        item = items.get(iid)
        label = f"{item['name']} +{item['level']}" if item else "Choose a weapon"
        action = f"inspect:{iid}" if iid else "collection"
        slots.append(f'<button class="wc-slot" data-opt="{e(action)}"><span>{n}</span>{e(label)}</button>')
    head = f'<p>Pack {data.get("pack_used", 0)} / {data.get("pack_cap", 6)} · town storage stays in Roothollow</p>' + '<div class="wc-deck" aria-label="Three battle weapons">' + ''.join(slots) + '</div>'
    materials=''.join(f'<div class="wc-item wc-material wc-{grade.lower()}" style="--grade:{COLORS[grade]}">'
        f'{icon(data.get("material_icons",{}).get(name,"shard"))}<span>{e(name)}</span>'
        f'<span>{data.get("materials",{}).get(name,0):,}</span></div>'
        for name,grade in data.get('material_grades',{}).items())
    if materials:
        head+='<details class="wc-materials"><summary>Upgrade materials</summary><div class="wc-grid">'+materials+'</div></details>'
    quiver=data.get('quiver',{})
    if quiver.get('types'):
        arrows=[]
        for arrow in quiver['types']:
            owned=''.join(f'<span style="color:{COLORS[offer["grade"]]}">{e(offer["grade"])}: {offer["owned"]:,}</span>'
                for offer in arrow['offers'])
            arrows.append(f'<div class="wc-item" style="--grade:#aab8b4">{icon("quiver")}'
                f'<span>{e(arrow["name"])}</span><span>{e(arrow["channel"])}</span>'
                f'<span>{e(arrow["effect"])}</span>{owned}</div>')
        equipped=''.join(f'<p>{e(bow["name"])}: {e(bow["grade"])} {e(bow["selected_name"])} · {bow["remaining"]:,} left</p>'
            for bow in quiver.get('bows',[]))
        head+=f'<details class="wc-quiver"><summary>Arrows · {quiver["used"]:,} / {quiver["capacity"]:,}</summary>'
        head+='<p>One arrow per shot, including a miss. Match the arrow grade to your bow.</p>'+equipped
        head+='<div class="wc-grid">'+''.join(arrows)+'</div><p>Buy bundles of 20 at the Forge arrow supplies rack. Choose a stocked payload on your bow during a group; selecting it is free.</p></details>'
    if not data.get("screen"):
        return '<section class="wc"><button class="wc-link" data-opt="collection">WEAPON COLLECTION</button>' + head + '</section>'
    cards = []
    for item in data["items"]:
        selected = item["id"] == data.get("selected")
        grade = item["grade"]
        url = art_url(item["image"])
        picture = f'<img src="{e(url)}" alt="{e(item["name"])}" loading="lazy">' if url else icon(item["path"])
        quote = item.get("quote")
        progress = []
        if quote:
            progress.append(f'{data["gold"]:,} / {quote["gold"]:,} gold')
            progress.extend(f'{name}: {data["materials"].get(name, 0):,} / {count:,}' for name, count in quote["materials"].items())
        else:
            progress.append("Original equipment kept" if item["source"] == "legacy" else "Maximum upgrade level")
        title = "; ".join(progress)
        cards.append(f'<button class="wc-item wc-{e(grade.lower())}{" chosen" if selected else ""}" '
            f'style="--grade:{COLORS[grade]}" data-opt="inspect:{e(item["id"])}" '
            f'aria-pressed="{str(selected).lower()}" title="{e(title)}">'
            f'<span class="wc-art">{picture}</span><span class="wc-name">{e(item["name"])}</span>'
            f'<span>{e(grade)} +{item["level"]} · {e(item["path"].title())}</span>'
            f'<span>{icon("weapon")} {item.get("current_attack",item["attack"]):,} ATK now / {item["attack"]:,} full</span>'
            f'<span>{item["durability"]:,} / {item["maximum"]:,} condition</span>'
            f'<meter min="0" max="{item["maximum"]}" value="{item["durability"]}" aria-label="Condition"></meter>'
            f'<span class="wc-effect">{e(item["effect"])}</span>'
            f'<span>{"In your deck" if item["selected"] else "In your collection"}</span></button>')
    details = ""
    selected = items.get(data.get("selected"))
    if selected:
        q = selected.get("quote")
        lines = [selected["description"], f'Received: {selected["source"]}', f'Location: {selected.get("location", "carried")}']
        if q:
            lines += [f'Next: +{q["level"]} · floor {q["floor"]}', f'Gold: {data["gold"]:,} / {q["gold"]:,}']
            lines += [f'{k}: {data["materials"].get(k, 0):,} / {v:,}' for k, v in q["materials"].items()]
            lines.append("Upgrade in the Forge")
            for site in data.get("resource_sites", []):
                if site["material"] in q["materials"]:
                    lines.append(f'{site["material"]}: {site["name"]} · floor {site["floor"]} · {site["tool_name"]} sold there for {site["price"]} gold')
        details = '<div class="wc-detail">' + ''.join(f'<p>{e(line)}</p>' for line in lines) + '</div>'
    return '<section class="wc">' + head + '<div class="wc-grid">' + ''.join(cards) + '</div>' + details + '</section>'


CSS = """
.wc,.wc button,.wc p,.wc span{font-family:VGA,monospace;font-size:16px;line-height:1.4;}
.wc{padding:16px;color:#e7e6d2;background:#111b1e;}
.wc button{color:inherit;cursor:pointer;border-radius:0;}
.wc-deck{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:16px;}
.wc-slot{background:#1b2b30;border:1px solid #526369;text-align:left;padding:8px;overflow-wrap:anywhere;}
.wc-slot>span{display:block;color:#e3c375;}
.wc-link{background:none;border:0;padding:0;margin-bottom:8px;color:#e3c375!important;}
.wc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;}
.wc-item{position:relative;display:flex;flex-direction:column;gap:6px;align-items:stretch;text-align:left;
 background:#19272b;border:2px solid var(--grade);padding:12px;min-width:0;}
.wc-item.wc-rare{box-shadow:inset 0 0 0 3px #111b1e,inset 0 0 0 4px var(--grade);}
.wc-item.wc-epic{border-style:double;border-width:6px;clip-path:polygon(8px 0,calc(100% - 8px) 0,calc(100% - 8px) 4px,100% 4px,100% calc(100% - 4px),calc(100% - 8px) calc(100% - 4px),calc(100% - 8px) 100%,8px 100%,8px calc(100% - 4px),0 calc(100% - 4px),0 4px,8px 4px);}
.wc-item.wc-legendary{border-width:4px;box-shadow:4px 0 0 #5c4722,-4px 0 0 #5c4722,0 4px 0 #5c4722,0 -4px 0 #5c4722;}
.wc-item.wc-legendary:before{content:'◆  ◆  ◆';color:var(--grade);text-align:center;}
.wc-item:focus-visible,.wc-item.chosen{outline:2px solid #68d6c1;outline-offset:4px;}
.wc-art{height:160px;display:grid;place-items:center;background:#0c1416;}
.wc-art img{max-width:100%;height:160px;object-fit:contain;image-rendering:pixelated;}
.wc-name,.wc-effect{color:var(--grade);}
.wc meter{width:100%;height:8px;accent-color:var(--grade);}
.wc-detail{margin-top:16px;padding:12px;border:1px solid #526369;background:#0c1416;}
.wc-detail p{margin:0 0 8px;}
.wc-quiver{margin:12px 0}.wc-quiver summary{cursor:pointer;color:#e3c375}.wc-quiver .wc-grid{margin:12px 0}.wc-quiver .wc-item{overflow-wrap:anywhere}
@media(max-width:440px){.wc{padding:12px}.wc-deck{gap:4px}.wc-slot{padding:5px}.wc-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.wc-item{padding:8px}}
"""

CSS += "\n.wc-materials{margin:12px 0}.wc-materials summary{cursor:pointer;color:#e3c375}.wc-materials .wc-grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:12px 0}.wc-material{padding:8px;overflow-wrap:anywhere}.wc-material .ico{width:32px;height:32px}@media(max-width:600px){.wc-materials .wc-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}\n"
