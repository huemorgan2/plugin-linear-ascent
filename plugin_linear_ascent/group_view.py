"""Group battle presentation, using authoritative scene values only."""
from html import escape

COLOR = {'Common':'#b5c4bd', 'Power':'#e3a35e', 'Magic':'#bb92e8'}
ICON = {'Common':'shard', 'Power':'t_armor', 'Magic':'t_resist'}


def render(group, owned, options, art_url, icon):
    e = lambda x: escape(str(x), quote=True)
    monsters = group['members']
    active = monsters[group['index']]
    events = group.get('events', [])
    def popups(defender):
        return ''.join(f'<span class="gb-event" data-combat-event="{e(v["id"])}">'
            f'{icon(ICON[v["channel"]])} {e(v["channel"])} resisted · {v["damage"]}</span>'
            for v in events if v['kind'] == 'resist' and v['defender'] == defender)
    def picture(m):
        src = art_url(m['image'])
        return f'<img src="{e(src)}" alt="{e(m["name"])}">' if src else ''
    roster = ''.join(f'<div class="gb-member {"fallen" if m["killed"] else "current" if i == group["index"] else ""}" '
        f'title="{e(m["name"])} · {e(m["affinity"])} · {"Air" if m["air"] else "Ground"}">'
        f'{picture(m)}<span>{"×" if m["killed"] else i+1} {e(m["name"])}</span>'
        f'{popups(m["instance"]) if m["instance"] != active["instance"] else ""}</div>' for i,m in enumerate(monsters))
    badges = (f'<span style="color:{COLOR[active["affinity"]]}">{icon(ICON[active["affinity"]])} {e(active["affinity"])}</span>'
              f'<span>{icon("t_wing" if active["air"] else "shoes")} {"Air" if active["air"] else "Ground"}</span>')
    gap = ''.join(f'<span class="{"at" if n == active["gap"] else ""}">{label}</span>' for n,label in enumerate(('Contact','Near','Far','Cover')))
    energy = ('EXHAUSTED · ½ attack · −2 speed' if active['exhausted'] else 'ENERGY PAID · normal strength') if active['started'] else 'WAITING · 1 energy when this enemy begins'
    haul = group['haul']
    materials = ' · '.join(f'{e(k)} ×{v}' for k,v in haul['materials'].items())
    items = {i['id']:i for i in (owned or {}).get('items',[])}
    cells=[]
    for iid in (owned or {}).get('deck',[]):
        item=items.get(iid)
        if item:
            src=art_url(item['image'])
            cells.append(f'<div class="gb-weapon"><img src="{e(src)}" alt="">'
                f'<span>{e(item["name"])} +{item["level"]}<br>{e(item["path"].title())} · {item["attack"]:,} ATK<br>'
                f'{item["durability"]}/{item["maximum"]}</span></div>')
        else:
            cells.append('<div class="gb-weapon">Empty slot</div>')
    actions = ''.join(f'<button class="opt gb-action {"locked" if o.locked else ""}" data-opt="{e(o.id)}" '
        f'aria-disabled="{str(o.locked).lower()}"><span class="key">[{n}]</span> '
        f'{e(o.label)}<span class="gb-hint">{e(o.hint)}</span></button>' for n,o in enumerate(options,1))
    rates=active.get('rates',{})
    drops=''.join(f'<span>{grade}: {rates.get("material",{}).get(grade,0):.4g}% material · '
        f'{rates.get("weapon",{}).get(grade,0):.4g}% weapon</span>' for grade in ('Common','Rare','Epic','Legendary'))
    log=''.join(f'<p>{e(v["text"])}</p>' for v in events)
    return (f'<section class="gb"><div class="gb-roster">{roster}</div>'
        f'<div class="gb-foe">{picture(active)}{popups(active["instance"])}</div>'
        f'<div class="gb-badges">{badges}<span>{icon("t_speed")} {active["speed"]} speed</span></div>'
        f'<p>{active["atk"]:,} ATK · {active["defense"]:,} DEF · Power ×{active["power"]} · Magic ×{active["magic"]}</p>'
        f'<details class="gb-drops"><summary>Drop chances for this enemy</summary>{drops}<p>Materials roll independently by grade. At most one weapon. Secure drops by clearing the group.</p></details>'
        f'<div class="gb-health">{icon("heart")} {active["hp"]:,} / {active["hp_max"]:,} HP'
        f'<meter min="0" max="{active["hp_max"]}" value="{active["hp"]}"></meter></div>'
        f'<div class="gb-gap">{gap}</div><p class="gb-energy">{energy}</p>'
        f'<div class="gb-haul">{group["xp"]} XP kept · {haul["gold"]:,} gold pending'
        f'{" · " + materials if materials else ""}</div><div class="gb-weapons">{"".join(cells)}</div>'
        f'<div class="gb-actions">{actions}</div><div class="gb-log" role="log">{log}</div></section>')


CSS = '''
.gb,.gb *{font-family:VGA,monospace;font-size:16px;line-height:1.35;box-sizing:border-box}
.gb{background:#111b1e;color:#e5e4cf;padding:16px}
.gb-roster{display:flex;gap:8px;margin-bottom:16px;overflow-x:auto;padding-top:8px}
.gb-member{position:relative;border:1px solid #485a60;min-width:80px;flex:1;max-width:130px;background:#1b2b30}
.gb-member img{width:100%;height:50px;object-fit:cover;image-rendering:pixelated}
.gb-member span{display:block;padding:4px;overflow-wrap:anywhere}
.gb-member.current{border:2px solid #e6bf68}.gb-member.fallen img{opacity:.3}.gb-member.fallen>span{text-decoration:line-through}
.gb-foe{position:relative;background:#0a1012;border:1px solid #40545a;height:192px;display:grid;place-items:center}
.gb-foe>img{width:100%;height:100%;object-fit:contain;image-rendering:pixelated}
.gb-badges{display:flex;flex-wrap:wrap;gap:16px;padding:12px 0}
.gb-health meter{display:block;width:100%;height:10px;margin:6px 0 12px;accent-color:#64d4be}
.gb-gap{display:grid;grid-template-columns:repeat(4,1fr);gap:4px}
.gb-gap span{border:1px solid #3d5056;padding:6px;text-align:center}.gb-gap .at{background:#25463e;border-color:#64d4be;color:#8de0cb}
.gb-drops{padding:8px 0}.gb-drops span{display:block}.gb-drops summary{cursor:pointer;color:#e6bf68}
.gb-energy{color:#e6bf68}.gb-haul{padding:10px;border:1px solid #e6bf68;background:#1b2b30}
.gb-weapons{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0}
.gb-weapon{background:#17262b;border:1px solid #40565f;padding:8px;display:flex;gap:8px;overflow-wrap:anywhere}
.gb-weapon img{width:28px;height:54px;object-fit:contain;image-rendering:pixelated}
.gb-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.gb-action.opt{white-space:normal!important;padding:10px!important;text-align:left;border:1px solid #496069;background:#203139;color:#e5e4cf;cursor:pointer;border-radius:0}
.gb-action.opt:hover,.gb-action.opt:focus-visible{border-color:#e6bf68;background:#30464f}.gb-action.locked{opacity:.55}
.gb-hint{display:block;color:#afc3c1}.gb-log p{margin:8px 0;border-bottom:1px solid #25383d;padding-bottom:6px}
.gb-event{display:none;position:absolute;z-index:2;left:10%;bottom:35%;padding:6px!important;background:#090f13;color:#e4bf7a;box-shadow:3px 3px #000;pointer-events:none;white-space:normal}
.gb-event.play{display:block;animation:gb-rise 1.4s steps(12,end) forwards}
@keyframes gb-rise{0%{transform:translateY(0);opacity:1}75%{opacity:1}100%{transform:translateY(-48px);opacity:0}}
@media(prefers-reduced-motion:reduce){.gb-event.play{animation:none;position:static;display:inline-block}}
@media(max-width:440px){.gb{padding:10px}.gb-foe{height:150px}.gb-weapons{gap:4px}.gb-weapon{display:block;padding:5px}.gb-weapon img{height:44px}.gb-actions{gap:6px}.gb-action.opt{padding:7px!important}}
'''
