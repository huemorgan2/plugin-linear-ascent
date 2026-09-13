"""Pure shared combat calculations used by the resolver and its wiki examples."""
import math
from .. import economy
from . import collection


def contribution(item):
    full = collection.stats(item)['attack']
    fraction = max(0, min(1, item['durability'] / max(1,item['maximum'])))
    if item['durability'] <= 0:
        return 0
    if item.get('legacy'):
        return full  # Retained old equipment keeps its earned contribution.
    if item['source'] == 'starter' and item['grade'] == 'Common':
        fraction = .5 + .5 * fraction
    return max(1, round(full * fraction))


def attack(p, item):
    path = collection.stats(item)['path']
    rank = max(0, min(10,int((p.get('training') or {}).get(path,0))))
    studies = sum(bool(v) for v in (p.get('mastery') or {}).values())
    return economy.player_atk(p['level'], contribution(item)) * (.8 + .04*rank) * (1 + economy.MASTERY_ATK_BONUS*studies)


def affinity(monster, channel, *, focus=False):
    mult = monster[channel.lower()]
    if focus and channel == 'Magic' and not monster['air'] and .4 <= mult < .75:
        return .75
    return mult


def hp_damage(amount, defense, multiplier, *, dot=False):
    return max(1, round(amount*multiplier - (0 if dot else defense*.35)))


def impact(family, gap, arrow=None, *, skill=False):
    """Source-channel/impact factors; defensive affinity is applied separately."""
    path=family['path'].lower()
    cfg=family['modifiers']
    channel='Magic' if path=='staff' else 'Power'
    factor=1
    if arrow and path=='bow':
        channel=arrow['channel']
        factor*=arrow['impact']*(cfg.get('arcaneImpact',1) if arrow['id']=='arcane' else 1)
    if path=='bow' and gap==0:
        factor*=cfg['contact']
    if skill and gap>=cfg.get('skillMinGap',4):
        factor*=cfg.get('skillImpact',1)
    return channel,factor


def example_hit(family, monster, arrow, gap):
    """Normalized direct-hit illustration, generated in Python for the wiki."""
    channel,factor=impact(family,gap,arrow)
    reach=not(family['path']=='Blade' and (monster['air'] or gap>0))
    amount=round(100*family['factor']*factor)
    multiplier=affinity(monster,channel)
    return dict(channel=channel,reach=reach,multiplier=multiplier,
        damage=hp_damage(amount,20,multiplier) if reach else 0)


def incoming(raw, armor, shield, *, guard=False):
    minimum = max(1, math.ceil(raw*.25))
    after_armor = max(minimum, round(raw-armor*.4))
    absorbed = min(max(0,after_armor-minimum),round(shield*(1.5 if guard else 1)))
    return dict(hp=after_armor-absorbed,armor=raw-after_armor,shield=absorbed,
        wear=max(1,math.ceil(absorbed/max(1,shield))) if absorbed else 0)
