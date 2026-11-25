"""Build all Chinese TTS boxes from the frozen, audited face mapping.

Run from the original repository after downloading the Chinese PDFs. The
mapping pins source hashes: changed PDFs require another layout audit, rather
than silently applying an English page map to a new Chinese edition.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote, unquote

import fitz

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = 'https://raw.githubusercontent.com/Wen-Qualtu/kt-datacards/main'
DEFAULT_BASE = 'https://raw.githubusercontent.com/megumi678/kt-datacards-cn/main'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def local_path(root, relative):
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f'Path outside root: {relative}')
    return result


def box_update_script(url):
    return '''
-- Chinese build: keep updates on this release's endpoint.
function performBoxUpdate(force)
    WebRequest.get(CHINESE_BOX_URL .. '?v=' .. tostring(os.time()), function(req)
        if req.is_error or tonumber(req.response_code) ~= 200 then
            broadcastToAll('中文资源加载失败，请检查网络及仓库地址。', {1,0.3,0.3})
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
'''.replace('CHINESE_BOX_URL', json.dumps(url))


def remove_superseded_cards(obj, removed_fronts):
    """Remove explicitly audited duplicate exports, keeping DeckIDs in sync."""
    removed = set()
    def clean(node, inherited=None):
        deck = node.get('CustomDeck', inherited or {})
        if 'CardID' in node:
            face = deck.get(str(node['CardID']//100), {}).get('FaceURL', '')
            rel = unquote(face[len(AUTHOR)+1:].split('?')[0]) if face.startswith(AUTHOR+'/') else ''
            if rel in removed_fronts:
                removed.add(rel)
                return None
        if 'ContainedObjects' in node:
            node['ContainedObjects'] = [v for child in node['ContainedObjects'] if (v := clean(child, deck)) is not None]
        if 'DeckIDs' in node:
            ids = [child['CardID'] for child in node.get('ContainedObjects', []) if 'CardID' in child]
            node['DeckIDs'] = ids
            keys = {str(i//100) for i in ids}
            node['CustomDeck'] = {k:v for k,v in deck.items() if k in keys}
        for state in node.get('States', {}).values():
            clean(state, deck)
        return node
    clean(obj)
    if removed != set(removed_fronts):
        raise ValueError(f'Obsolete card audit differs: {set(removed_fronts)-removed}')
    return len(removed)


def make_spawner(base):
    lua = (ROOT / 'config/defaults/tts-script/team-spawner-clean-script.lua').read_text('utf-8')
    lua = lua.replace(AUTHOR, base).replace('name = slugToName(slug)', 'name = entry.name or slugToName(slug)')
    for old, new in {
        'Kill Team Spawner': 'Kill Team 中文生成器',
        'Spawn a Kill Team': '选择中文队伍',
        'Spawn Team': '生成队伍',
        'Search teams...': '搜索中文名称或英文标识...',
        '>Close</Button>': '>关闭</Button>',
        'Loading teams from GitHub...': '正在从 GitHub 加载队伍列表...',
        'KILL TEAM SPAWNER': 'KILL TEAM 中文生成器',
        ' teams available.': ' 个队伍可用。',
        'Click 生成队伍 to pick or search a team.': '点击生成队伍选择或搜索。',
    }.items():
        lua = lua.replace(old, new)
    return {
        'GUID': 'c8a701', 'Name': 'BlockSquare', 'Nickname': 'Kill Team 中文生成器',
        'Description': '从 GitHub 加载中文卡盒。',
        'Transform': {'posX':0,'posY':2,'posZ':0,'rotX':0,'rotY':0,'rotZ':0,'scaleX':2,'scaleY':0.3,'scaleZ':2},
        'ColorDiffuse': {'r':0.12,'g':0.4,'b':0.3},
        'LuaScript':lua, 'LuaScriptState':'', 'XmlUI':'', 'Locked':False,
    }


def annotate_cards(node, notes, inherited=None):
    deck = node.get('CustomDeck', inherited or {})
    if 'CardID' in node:
        face = deck.get(str(node['CardID']//100), {}).get('FaceURL', '')
        for note in notes:
            if note['asset'] in unquote(face):
                node['Description'] = node.get('Description', '') + '\n' + note['note']
    for child in node.get('ContainedObjects', []):
        annotate_cards(child, notes, deck)


def build(output, base, selected=None):
    mapping_path = ROOT / 'config/chinese-face-map.json'
    mapping = read_json(mapping_path)
    teams = [t for t in mapping['teams'] if not selected or t in selected]
    if selected and set(selected) != set(teams):
        raise ValueError('Unknown team selection')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new, empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    # Validate all inputs before creating the release index.
    for team in teams:
        for face in mapping['teams'][team]['faces']:
            src = local_path(ROOT, face['source'])
            if not src.is_file() or digest(src) != face['source_sha256']:
                raise ValueError(f'PDF changed or missing; audit layout again: {src}')
    index, reports = {}, []
    own_pattern = re.compile(re.escape(base) + r'/([^\s"\\<>]+)')
    for team in teams:
        spec = mapping['teams'][team]
        box_rel = spec['box']
        obj = read_json(ROOT / box_rel)
        removed_count = remove_superseded_cards(obj, spec.get('remove_fronts', []))
        hashes = {}
        for face in spec['faces']:
            src = ROOT / face['source']
            target = local_path(output, face['asset'])
            target.parent.mkdir(parents=True, exist_ok=True)
            with fitz.open(src) as doc:
                if len(doc) != 1 or not re.search('[\u4e00-\u9fff]', doc[0].get_text()):
                    raise ValueError(f'Expected a single Chinese card face: {src}')
                doc[0].get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False).save(target, jpg_quality=95)
            hashes[face['asset']] = digest(target)[:12]

        def replace_url(match):
            tail = match.group(1)
            rel = unquote(tail.split('?')[0])
            if rel in hashes:
                return base + '/' + quote(rel, safe='/') + '?v=' + hashes[rel]
            return match.group(0)

        def rewrite(v):
            if isinstance(v, dict):
                return {k:rewrite(x) for k,x in v.items()}
            if isinstance(v, list):
                return [rewrite(x) for x in v]
            if isinstance(v, str):
                v = v.replace('local key = kfn != nil and kfn(v,c,t) or k',
                              'local key = kfn ~= nil and kfn(v,c,t) or k')
                return own_pattern.sub(replace_url, v.replace(AUTHOR, base))
            return v

        obj = rewrite(obj)
        annotate_cards(obj, spec.get('card_notes', []))
        box_url = base + '/' + quote(box_rel, safe='/')
        obj['Nickname'] = spec['name'] + ' - 中文卡盒'
        obj['Description'] = '官方中文卡面；保留原卡盒摆放、取牌和回收功能。自动属性沿用原模板。'
        obj['LuaScript'] = obj.get('LuaScript', '') + box_update_script(box_url)
        fronts = set()
        for node in walk(obj):
            for deck in node.get('CustomDeck', {}).values():
                url = deck['FaceURL']
                if not url.startswith(base + '/'):
                    raise ValueError(f'Unexpected card source: {url}')
                rel = unquote(url[len(base)+1:].split('?')[0])
                if rel not in hashes:
                    raise ValueError(f'Card front missing Chinese face: {rel}')
                fronts.add(rel)
        expected = {f['asset'] for f in spec['faces'] if f['side']=='front'}
        if fronts != expected:
            raise ValueError(f'Card/manifest mismatch: {team}: missing={expected-fronts}; extra={fronts-expected}')
        write_json(output / box_rel, obj)

        # Include referenced assets, including URLs embedded in LuaScriptState.
        # These are original meshes, generic backs, token and dice textures.
        pending = [output / box_rel]
        visited = set()
        while pending:
            path = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            text = path.read_text('utf-8').replace(AUTHOR, base)
            text = text.replace('local key = kfn != nil and kfn(v,c,t) or k',
                                'local key = kfn ~= nil and kfn(v,c,t) or k')
            text = own_pattern.sub(replace_url, text)
            for match in own_pattern.finditer(text):
                rel = unquote(match.group(1).split('?')[0])
                source, target = local_path(ROOT, rel), local_path(output, rel)
                if not target.exists() and source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    if target.suffix in ('.json', '.lua'):
                        pending.append(target)
            path.write_text(text, encoding='utf-8')
        index[team] = {'name':spec['name'], 'box':{'url':box_url}}
        reports.append({'team':team, 'name':spec['name'], 'cards':len(fronts), 'content_faces':len(hashes),
                        'removed_duplicate_cards':removed_count, 'source_notes':spec.get('card_notes', []),
                        'tts_client_verified':team=='angels-of-death'})
        if team == 'angels-of-death':
            write_json(output / 'SavedObjects/KT-Chinese-Angels-Box.json', {'SaveName':obj['Nickname'], 'ObjectStates':[obj]})
        print(f'{team}: {len(fronts)} cards, {len(hashes)} Chinese faces', flush=True)

    # Publish index only when every selected box has been built successfully.
    write_json(output / 'output/team-urls.json', index)
    spawner = make_spawner(base)
    write_json(output / 'SavedObjects/KT-Chinese-Spawner.json', {'SaveName':spawner['Nickname'], 'ObjectStates':[spawner]})
    (output / 'Install-SavedObjects.ps1').write_text('''$ErrorActionPreference = 'Stop'
$documents = [Environment]::GetFolderPath('MyDocuments')
if (-not $documents) { throw 'Windows Documents folder was not found.' }
$target = Join-Path $documents 'My Games\\Tabletop Simulator\\Saves\\Saved Objects\\KT Chinese GitHub'
New-Item -ItemType Directory -Path $target -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'SavedObjects') -Filter '*.json' -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $target $_.Name) -Force
}
Write-Host "Installed into: $target"
''', encoding='utf-8-sig')
    (output / 'Install.cmd').write_text('@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-SavedObjects.ps1"\npause\n', encoding='ascii')
    checks = validate(output, base)
    write_json(output / 'deployment.json', {'base_url':base, 'teams':reports, 'validated_asset_references':checks,
               'validation':'Static assets and Lua checks; only Angels of Death has user-confirmed in-game validation.'})
    sources = ['tools/build_chinese_all.py','tools/create_chinese_supplements.py','tools/verify_chinese_release.py',
               'config/chinese-face-map.json','config/defaults/tts-token/token-bag-script.lua','pipeline/steps/warcom/scraper.py']
    sources += [p.relative_to(ROOT).as_posix() for p in (ROOT/'layers/chinese-supplements').glob('*.pdf')]
    for relative in sources:
        target = output / 'source-patches' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    print(f'Built {len(index)} teams; validated {checks} asset references. {output}', flush=True)


def validate(output, base):
    checks = 0
    for path in list((output / 'output').rglob('*.json')) + list((output / 'SavedObjects').glob('*.json')):
        text = path.read_text('utf-8')
        if AUTHOR in text or 'http://127.0.0.1:' in text:
            raise ValueError(f'Stale URL: {path}')
        for node in walk(json.loads(text)):
            for key, val in node.items():
                if key.endswith('URL') and isinstance(val, str) and val.startswith(base+'/'):
                    target = local_path(output, unquote(val[len(base)+1:].split('?')[0]))
                    if not target.is_file():
                        raise ValueError(f'Missing asset in {path}: {target}')
                    checks += 1
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url', default=DEFAULT_BASE)
    parser.add_argument('--teams', help='Comma-separated slugs; default: all audited teams')
    args = parser.parse_args()
    build(args.output.resolve(), args.base_url.rstrip('/'), args.teams.split(',') if args.teams else None)
