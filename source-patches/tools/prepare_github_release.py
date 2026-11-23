"""Rebase the validated local TTS deployment to a user's GitHub repository."""
import argparse
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = 'https://raw.githubusercontent.com/Wen-Qualtu/kt-datacards/main'
LOCAL = 'http://127.0.0.1:18765'


def prepare(local, output, repo, branch='main'):
    match = re.fullmatch(r'https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)/?', repo)
    if not match or not re.fullmatch(r'[A-Za-z0-9_.-]+', branch):
        raise ValueError('Use https://github.com/OWNER/REPO and a simple branch name.')
    base = f'https://raw.githubusercontent.com/{match[1]}/{match[2]}/{branch}'
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be empty; choose a new release directory.')
    shutil.copytree(local / 'site', output, dirs_exist_ok=True)
    shutil.copytree(local / 'SavedObjects', output / 'SavedObjects')
    # Every generated JSON is rebased, including individual object exports.
    # Leave third-party model repositories unchanged.
    pending = [p for p in output.rglob('*') if p.suffix in ('.json', '.lua')]
    processed = set()
    while pending:
        p = pending.pop()
        if p in processed:
            continue
        processed.add(p)
        text = p.read_text(encoding='utf-8')
        text = text.replace(LOCAL, base).replace(AUTHOR, base)
        text = text.replace('中文服务未连接，请先启动本机服务。', '中文资源加载失败，请检查网络及仓库地址。')
        text = text.replace('先启动中文资源服务，再点击生成队伍。', '点击生成队伍，从 GitHub 加载中文卡盒。')
        text = text.replace('Kill Team 中文生成器（本机测试）', 'Kill Team 中文生成器')
        for tail in re.findall(re.escape(base) + r'/([^\s"\\]+)', text):
            rel = unquote(tail.split('?')[0])
            # Only complete static paths are copied; Lua builds some at runtime.
            source = ROOT / rel
            target = output / rel
            if source.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                if target.suffix in ('.json', '.lua'):
                    pending.append(target)
        if p.suffix == '.json':
            json.loads(text)
        p.write_text(text, encoding='utf-8')
    shutil.copy2(local / 'Install-SavedObjects.ps1', output / 'Install-SavedObjects.ps1')
    installer = output / 'Install-SavedObjects.ps1'
    installer.write_text(installer.read_text().replace('KT Chinese Local', 'KT Chinese GitHub'), encoding='utf-8')
    (output / 'Install.cmd').write_text('@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-SavedObjects.ps1"\npause\n', encoding='ascii')
    patches = output / 'source-patches'
    for name in ('pipeline/steps/warcom/scraper.py', 'tools/build_chinese_local.py',
                 'tools/prepare_github_release.py', 'pyproject.toml', 'poetry.lock'):
        dest = patches / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    (output / 'deployment.json').write_text(json.dumps({'repository':repo,'branch':branch,'base_url':base,'team':'angels-of-death','tts_client_verified':False},indent=2),encoding='utf-8')
    # Static references in runtime JSON must resolve to actual uploaded files.
    def nodes(v):
        if isinstance(v,dict):
            yield v
            for child in v.values():yield from nodes(child)
        elif isinstance(v,list):
            for child in v:yield from nodes(child)
    checks = 0
    for p in list((output/'output').rglob('*.json')) + list((output/'SavedObjects').glob('*.json')):
        text=p.read_text(encoding='utf-8')
        assert LOCAL not in text and AUTHOR not in text, p
        for node in nodes(json.loads(text)):
            for key,value in node.items():
                if key.endswith('URL') and isinstance(value,str) and value.startswith(base+'/'):
                    path=output / unquote(value[len(base)+1:].split('?')[0])
                    if not path.is_file():raise ValueError(f'Missing resource: {path}')
                    checks += 1
    print(f'Ready: {output}; checked {checks} resource references; {base}')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repo',required=True)
    parser.add_argument('--branch',default='main')
    args=parser.parse_args()
    prepare(args.local,args.output,args.repo,args.branch)
