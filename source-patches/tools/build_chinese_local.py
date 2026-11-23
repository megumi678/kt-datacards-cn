"""Build a localized copy of the original AoD TTS box and original spawner.

Uses an audited mapping for the currently downloaded Chinese PDF. It intentionally
rejects other teams rather than guessing English/Chinese pagination matches.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

import fitz

ROOT = Path(__file__).resolve().parents[1]
TEAM = 'angels-of-death'
ORIGIN = 'https://raw.githubusercontent.com/Wen-Qualtu/kt-datacards/main'
TITLES = {
    'space-marine-captain': '星际战士连长',
    'assault-intercessor-sergeant': '突击仲裁者军士',
    'intercessor-sergeant': '仲裁者军士',
    'assault-intercessor-grenadier': '突击仲裁者掷弹兵',
    'assault-intercessor-warrior': '突击仲裁者战士',
    'heavy-intercessor-gunner': '重装仲裁者炮手',
    'intercessor-gunner': '仲裁者炮手',
    'intercessor-warrior': '仲裁者战士',
    'eliminator-sniper': '歼灭者狙击手',
    'purity-seals': '纯洁印章', 'chapter-reliquaries': '战团圣物',
    'tilting-shields': '偏移肩盾', 'auspex': '占卜仪',
    'chapter-tactics': '战团战术', 'astartes': '阿斯塔特',
    'adjust-doctrine': '调整条令', 'transhuman-physiology': '超人体格',
    'shock-assault': '震慑突袭', 'wrath-of-vengeance': '复仇之怒',
    'operative-selection': '杀戮小队', 'combat-doctrine': '战斗条令',
    'and-they-shall-know-no-fear': '他们无所畏惧',
    'adaptive-tactics': '灵活战术', 'indomitus': '不屈不挠',
}


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def visit(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from visit(child)
    elif isinstance(value, list):
        for child in value:
            yield from visit(child)


def build(destination, base):
    site = destination / 'site'
    site.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / f'layers/integration/{TEAM}/manifest.json').read_text(encoding='utf-8'))
    obj = json.loads((ROOT / f'output/{TEAM}/tts_objects/Angels Of Death.json').read_text(encoding='utf-8'))
    shutil.copytree(ROOT / f'output/{TEAM}', site / f'output/{TEAM}', dirs_exist_ok=True)
    replacements = {}
    audit = []
    for category, entries in manifest.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            name = slug(entry['name'])
            expected = TITLES[name]
            prefix = name if category == 'datacards' else f'{TEAM}-{name}'
            for card in entry['cards']:
                suffix = f"-card{card['card_number']}" if len(entry['cards']) > 1 else ''
                for side in ('front', 'back'):
                    if side not in card:
                        continue
                    pdf = ROOT / card[side]
                    with fitz.open(pdf) as doc:
                        text = re.sub(r'\s+', '', doc[0].get_text())
                        if not re.search('[\u4e00-\u9fff]', text):
                            raise ValueError(f'Not Chinese: {pdf}')
                        # Continuations can omit the heading. Audit first fronts.
                        if side == 'front' and card['card_number'] == 1 and expected not in text:
                            raise ValueError(f'Wrong source layout, expected {expected}: {pdf}')
                        name_out = f'{prefix}{suffix}-{side}.jpg'
                        relative = f'output/{TEAM}/cards/{category}/{name_out}'
                        target = site / relative
                        if not target.exists():
                            raise ValueError(f'Original asset missing: {relative}')
                        doc[0].get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False).save(target, jpg_quality=95)
                    replacements[relative] = hashlib.sha256(target.read_bytes()).hexdigest()[:12]
                    audit.append({'asset': relative, 'source': card[side], 'expected_title': expected})
    if len(audit) != 31:
        raise ValueError(f'Expected 31 content faces (excluding notes), got {len(audit)}')

    def rewrite(v):
        if isinstance(v, dict):
            return {k: rewrite(x) for k, x in v.items()}
        if isinstance(v, list):
            return [rewrite(x) for x in v]
        if isinstance(v, str):
            # Rewrite URLs embedded in scripts/states as well as CustomDeck.
            v = v.replace(ORIGIN, base)
            if v.startswith(base + '/output/') and '\n' not in v:
                rel = unquote(urlsplit(v).path.lstrip('/'))
                # The local base has no path prefix; support hosted bases too.
                rel = unquote(v[len(base) + 1:].split('?')[0])
                if rel in replacements:
                    v = f'{base}/{rel}?v={replacements[rel]}'
            return v
        return v

    obj = rewrite(obj)
    obj['Nickname'] = '死亡天使 - 中文卡盒'
    obj['Description'] = '中文卡面；保留原卡盒取牌、摆放、回收逻辑。自动属性仍使用原始英文数据。'
    # Override only the network updater, preventing Update/Reset from restoring
    # the original English box. Existing local reset/recall code stays intact.
    obj['LuaScript'] += '''\n
-- Chinese build: updates must stay on the Chinese endpoint.
function performBoxUpdate(force)
    WebRequest.get(CHINESE_BOX_URL .. '?v=' .. tostring(os.time()), function(req)
        if req.is_error or tonumber(req.response_code) ~= 200 then
            broadcastToAll('中文服务未连接，请先启动本机服务。', {1,0.3,0.3})
            return
        end
        local ok, data = pcall(JSON.decode, req.text)
        if not ok or type(data) ~= 'table' or not data.Name then
            broadcastToAll('中文卡盒数据无效。', {1,0.3,0.3})
            return
        end
        local box = spawnObjectData({data=data,
            position=self.getPosition()+Vector(5,1,0), rotation=self.getRotation()})
        if box then broadcastToAll('已在旁边生成最新中文卡盒。', {0.2,1,0.2}) end
    end)
end
'''.replace('CHINESE_BOX_URL', json.dumps(base + '/output/' + TEAM + '/tts_objects/Angels%20Of%20Death.json'))

    fronts = set()
    for node in visit(obj):
        for deck in node.get('CustomDeck', {}).values():
            rel = unquote(deck['FaceURL'][len(base) + 1:].split('?')[0])
            if rel not in replacements:
                raise ValueError(f'Untranslated front: {rel}')
            fronts.add(rel)
    if len(fronts) != 25:
        raise ValueError(f'Expected 25 playable cards, got {len(fronts)}')

    # Copy original mesh, dice and generic visual resources used by the box.
    serialized = json.dumps(obj, ensure_ascii=False)
    for tail in re.findall(re.escape(base) + r'/([^\s"\\]+)', serialized):
        rel = unquote(tail.split('?')[0])
        source = ROOT / rel
        if source.is_file():
            target = site / rel
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    (site / f'output/{TEAM}/tts_objects/Angels Of Death.json').write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    index = {TEAM: {'name': '死亡天使', 'box': {'url': base + f'/output/{TEAM}/tts_objects/Angels%20Of%20Death.json'}}}
    (site / 'output/team-urls.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
    lua = (ROOT / 'config/defaults/tts-script/team-spawner-clean-script.lua').read_text(encoding='utf-8')
    lua = lua.replace(ORIGIN, base).replace('name = slugToName(slug)', 'name = entry.name or slugToName(slug)')
    lua = lua.replace('Kill Team Spawner', 'Kill Team 中文生成器').replace('Spawn Team', '生成队伍')
    spawner = {
        'GUID': 'c8a701', 'Name': 'BlockSquare', 'Nickname': 'Kill Team 中文生成器（本机测试）',
        'Description': '先启动中文资源服务，再点击生成队伍。',
        'Transform': {'posX':0,'posY':2,'posZ':0,'rotX':0,'rotY':0,'rotZ':0,'scaleX':2,'scaleY':0.3,'scaleZ':2},
        'ColorDiffuse': {'r':0.12,'g':0.4,'b':0.3},
        'LuaScript': lua, 'LuaScriptState':'', 'XmlUI':'', 'Locked':False,
    }
    saved = destination / 'SavedObjects'
    saved.mkdir(exist_ok=True)
    for filename, item in [('KT-Chinese-Spawner.json', spawner), ('KT-Chinese-Angels-Box.json', obj)]:
        (saved / filename).write_text(json.dumps({'SaveName':item['Nickname'], 'ObjectStates':[item]}, ensure_ascii=False, indent=2), encoding='utf-8')
    (destination / 'audit.json').write_text(json.dumps({'cards':25,'content_faces':31,'mapping':audit}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Built original-script Chinese box: 25 cards / 31 content faces; source-title checks passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url', default='http://127.0.0.1:18765')
    args = parser.parse_args()
    build(args.output.resolve(), args.base_url.rstrip('/'))
