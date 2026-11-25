"""Validate a generated release and exercise its Lua spawner with TTS mocks.

Requires Pillow and lupa in the build environment. This is not an in-game test.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote

from PIL import Image
from lupa import LuaRuntime

from build_chinese_all import read_json, validate, walk


def verify(root):
    deployment = read_json(root/'deployment.json')
    base = deployment['base_url']
    refs = validate(root, base)
    index = read_json(root/'output/team-urls.json')
    lua = LuaRuntime(unpack_returned_tuples=True)
    compile_lua = lua.eval('function(s) local f,e=load(s); return f~=nil,e end')
    scripts = set()
    cards = 0
    for entry in index.values():
        relative = unquote(entry['box']['url'][len(base)+1:])
        obj = read_json(root/relative)
        for node in walk(obj):
            if node.get('LuaScript'):
                scripts.add(node['LuaScript'])
            if node.get('LuaScriptState'):
                json.loads(node['LuaScriptState'])
            if 'CardID' in node:
                cards += 1
            if 'DeckIDs' in node:
                assert node['DeckIDs']==[c['CardID'] for c in node['ContainedObjects']]
                for card_id in node['DeckIDs']:
                    assert str(card_id//100) in node['CustomDeck']
    spawner = read_json(root/'SavedObjects/KT-Chinese-Spawner.json')['ObjectStates'][0]
    scripts.add(spawner['LuaScript'])
    for source in scripts:
        ok, error = compile_lua(source)
        assert ok,error
    images = 0
    for path in (root/'output').rglob('*.jpg'):
        with Image.open(path) as im:
            im.verify()
        images += 1
    calls, spawned, messages = [], [], []
    def to_lua(value):
        if isinstance(value, dict):
            return lua.table_from({k:to_lua(v) for k,v in value.items()})
        if isinstance(value, list):
            return lua.table_from([to_lua(v) for v in value])
        return value
    def web_get(url, callback):
        assert url.startswith(base+'/'),url
        relative = unquote(url[len(base)+1:].split('?')[0])
        calls.append(relative)
        payload = (root/relative).read_text('utf-8')
        callback(to_lua({'text':payload,'response_code':200,'is_error':False,'error':''}))
    def spawn(parameters):
        obj = json.loads(parameters['json'])
        assert obj['Name']=='Custom_Model_Bag'
        spawned.append(obj['Nickname'])
        return True
    lua.globals().JSON = lua.table_from({'decode':lambda s:to_lua(json.loads(s))})
    lua.globals().WebRequest = lua.table_from({'get':web_get})
    lua.globals().spawnObjectJSON = spawn
    lua.globals().captureMessage = lambda *args:messages.append(str(args[0]))
    lua.execute('''
local vectorMeta = {__add=function(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end}
function Vector(x,y,z) return setmetatable({x=x,y=y,z=z},vectorMeta) end
Physics={cast=function(_) return {} end}
Player={White={broadcast=captureMessage}}
broadcastToAll=captureMessage
print=captureMessage
self={setName=function(_) end,setDescription=function(_) end,createButton=function(_) end,
 getScale=function() return {x=2,y=0.3,z=2} end,
 getBoundsNormalized=function() return {size={x=2,y=0.3,z=2}} end,
 getPosition=function() return Vector(0,2,0) end,
 UI={setXml=function(xml) menuXml=xml end,setAttribute=function(...) end}}
''')
    lua.execute(spawner['LuaScript'])
    lua.globals().onLoad()
    lua.globals().onSpawnClick(None, 'White')
    xml = lua.globals().menuXml
    assert xml.count('id="team_')==len(index)
    for entry in index.values():
        assert entry['name'] in xml
    for i in range(1,len(index)+1):
        lua.globals().spawnerChooseTeam(to_lua({'color':'White'}),None,f'team_{i}')
    assert len(spawned)==len(index)
    assert len(set(spawned))==len(index)
    assert set(calls[1:])=={unquote(e['box']['url'][len(base)+1:]) for e in index.values()}
    assert not any('Failed' in m or 'failed' in m or '错误' in m for m in messages),messages
    report = {'teams':len(index),'cards':cards,'jpeg_files':images,
              'asset_references':refs,'unique_lua_scripts_compiled':len(scripts),
              'mock_spawns':len(spawned),'in_game_validation':'User confirmed Angels of Death; remaining teams require TTS smoke testing.'}
    (root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release',type=Path)
    verify(parser.parse_args().release)
