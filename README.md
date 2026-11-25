# Kill Team 中文卡盒：48 队版

本包供 Tabletop Simulator 的中文队伍生成器使用，固定资源地址为：
https://raw.githubusercontent.com/megumi678/kt-datacards-cn/main

包含 48 个队伍、1,298 张卡牌。保留原卡盒的取牌、Place 摆放、Recall 回收功能。
队伍菜单支持中文名称及英文队伍标识搜索。卡盒外观、卡背、标记和自动属性沿用原模板，因此部分名称、按钮和属性文本仍是英文。

## 上传到你的 GitHub

将本文件夹**里面的内容**合并到 megumi678/kt-datacards-cn 仓库的 main 分支根目录。
正确路径是 output/team-urls.json；不能多套一层 Chinese-48-Teams/output。
仅上传 ZIP 压缩包不能让游戏加载资源，必须上传解压后的文件与文件夹。

这是约 535 MiB、3,600 多个文件的资源包，建议使用 GitHub Desktop 上传。

1. 打开 GitHub Desktop 并登录 megumi678。
2. File → Clone repository → URL，填写 https://github.com/megumi678/kt-datacards-cn 。
3. Local path 选择新的目录，例如 D:\TTF\kt-datacards-cn-publish，然后点击 Clone。
4. 打开克隆完成的目录。把本包里面的 output、SavedObjects、source-patches 及根目录文件全部复制进去，遇到同名文件选择替换。保留克隆目录的 .git 文件夹。
5. 回到 GitHub Desktop，确认当前仓库是 megumi678/kt-datacards-cn、分支是 main。Summary 填写 Add 48 Chinese teams。
6. 点击 Commit to main（或 Commit ... files to main），再点击 Push origin。上传完成后，在网页上打开 output/team-urls.json，应包含 48 个队伍条目。

官方操作说明：
- https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-and-forking-repositories-from-github-desktop
- https://docs.github.com/en/desktop/making-changes-in-a-branch/committing-and-reviewing-changes-to-your-project-in-github-desktop

## 在游戏里使用

务必先完成上传。安装新版生成器不会替你上传资源；GitHub 仍是旧版时，游戏菜单仍只有死亡天使。

1. 在解压后的本包目录双击 Install.cmd。它只把生成器和死亡天使示例卡盒复制到 Windows 文档中的 TTS Saved Objects。
2. 启动 TTS，进入房间，打开 Objects（对象）→ Saved Objects（已保存物品）→ KT Chinese GitHub。
3. 把 Kill Team 中文生成器放到桌面。已经放在桌面的旧生成器不会自动重新读取队伍列表；请重新放置生成器，或重新载入房间。
4. 点击“生成队伍”，从 48 个队伍中选择一个。等待下载完成后，桌面会出现该队伍的卡盒。
5. 点卡盒的 Place 摆放牌组；也可以从盒子里取出物品。使用 Recall 回收。
6. 鼠标放在卡牌上按 F 翻面，按住 Alt 放大查看。看到阵营图标通常是在看卡背。
7. 联机时朋友通过房间加载同一批在线资源。朋友不必安装 Python 或运行抓取程序，需要能访问 GitHub 原始资源地址。

这是卡盒与规则牌生成器，保留原模板提供的物品，不额外生成完整战棋模型队伍。

## 本版修复与来源说明

- 从官方简体中文 PDF 生成卡面；为屠戮之翼补全原 kt-app 来源与中文 PDF 的映射。
- 清除原导出卡盒中 24 张已由新清单替代的重复旧卡，保持牌组 CardID 对应关系。
- 强征小队的独立选人卡在本次官方中文 PDF 中缺失：从同一 PDF 第 15 页附录裁剪并整理为两面。
- 执政官之手的大享乐者数据卡在本次官方中文 PDF 中缺失：本包提供明确标注“中文补译（非官方）”的替代卡，基于原模板英文卡翻译，数值沿用原模板。请对战前核对版本。
- 原 token-bag Lua 中的 != 改为 Lua 标准的 ~=。
- 卡盒更新功能保持指向中文仓库，避免重新生成英文卡盒。
- 图片为对应语言文件的内容；本版没有重新解析或更新自动属性，自动属性与卡面有差异时请以所使用的规则版本为准。

原项目：https://github.com/Wen-Qualtu/kt-datacards
官方规则来源：https://www.warhammer-community.com/en-gb/downloads/kill-team/ （下载语言：简体中文）

## 验证范围

已完成：48 队菜单与逐队生成的模拟测试、4,478 处本仓库资源引用检查、59 段不同 Lua 脚本的语法检查、全部导出 JPEG 可解码检查，以及逐队代表卡和补充卡的图片检查。
用户已在 TTS 中确认死亡天使可用；其余 47 队尚未逐队进行实际 TTS 客户端测试。validation.json 记录检查结果。

## 文件用途

- output/：游戏加载的 48 队卡盒 JSON、图片、模型与队伍目录，必须完整上传。
- SavedObjects/：本地安装的生成器和示例卡盒。
- Install.cmd、Install-SavedObjects.ps1：安装上述物品。
- source-patches/：本次修改的代码、固定来源映射与补充 PDF，供维护者合并到原项目。
- teams.csv：中文队伍名称、英文标识与卡牌数量。
- deployment.json、validation.json：构建及检查记录。

source-patches 是原项目的覆盖补丁，不是完整源码仓库，也不包含虚拟环境、缓存和全部下载 PDF。
构建者应把 source-patches 中的内容合并到原项目根目录，准备好相同的官方中文裁剪 PDF，然后运行：

```powershell
.\.venv\Scripts\python.exe tools\build_chinese_all.py --output D:\TTF\Chinese-48-Rebuild
```

构建器会核对固定的 PDF 哈希；如果官方下载内容发生变化，会停止并要求重新核对布局，防止卡面错配。修改仓库地址时可使用 --base-url。
