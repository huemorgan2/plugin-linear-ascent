"""Forge catalog cards; all prices and actions originate in the engine."""
from html import escape
from .collection_view import COLORS


def render(data, options, art_url, icon):
    e=lambda value:escape(str(value),quote=True)
    indexed={o.id:(n,o) for n,o in enumerate(options,1)}
    def button(oid,label=None,cls=''):
        n,o=indexed[oid]
        return (f'<button class="ws-action {cls}" data-opt="{e(oid)}" aria-disabled="{str(o.locked).lower()}">'
            f'[{n}] {e(label or o.label)}<span>{e(o.hint)}</span></button>')
    grades=[]
    for grade,color in COLORS.items():
        grades.append(f'<div class="wc-item wc-{grade.lower()}" style="--grade:{color}">'
            +button('shop_grade:'+grade,grade, 'chosen' if grade==data['grade'] else '')+'</div>')
    cards=[]
    for item in data['items']:
        grade=item['grade'];family=item['family'];src=art_url(item['image'])
        cards.append(f'<article class="wc-item wc-{grade.lower()}" style="--grade:{COLORS[grade]}">'
            f'<div class="wc-art"><img src="{e(src)}" alt="{e(item["name"])}" loading="lazy"></div>'
            f'<p class="wc-name">{e(item["name"])} · {grade} +{item["level"]}</p>'
            f'<p>{icon("weapon")} {item["attack"]:,} ATK · {e(item["path"].title())}<br>'
            f'{item["maximum"]:,} condition · fully repaired</p><p class="wc-effect">{e(item["effect"])}</p>'
            f'<p>{e(item["description"])}</p>'+button(f'forge_buy:{family}:{grade}','Buy')
            +button(f'forge_craft:{family}:{grade}','Craft at +0')+'</article>')
    return '<section class="wc ws"><div class="ws-grades">'+''.join(grades)+'</div><div class="wc-grid">'+''.join(cards)+'</div>'+button('shop_back')+'</section>'

CSS='''
.ws p{margin:4px 0}.ws-grades{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:24px}
.ws-grades .wc-item{padding:4px;justify-content:center}.ws-grades .ws-action{height:100%;border:0;margin:0}
.ws-grades .chosen{background:#304944;outline:2px solid #66d4bd}
.ws-action{background:#203139;border:1px solid #496069;color:#e5e4cf;padding:10px;text-align:left;cursor:pointer;margin-top:8px}
.ws-action span{display:block;color:#afc3c1}.ws-action[aria-disabled=true]{opacity:.5}
.ws-action:hover,.ws-action:focus-visible{outline:2px solid #66d4bd;outline-offset:2px}
@media(max-width:440px){.ws-grades{grid-template-columns:repeat(2,minmax(0,1fr))}.ws .wc-grid{grid-template-columns:1fr}}
'''
