# Kill Team 中文卡牌 · Tabletop Simulator

为 Tabletop Simulator（TTS）提供 Kill Team 中文规则卡牌与队伍卡盒。当前资源包覆盖 **48 个队伍、1,298 张卡牌**，可在游戏内搜索队伍并生成对应卡盒。

本项目基于 [kt-datacards](https://github.com/Wen-Qualtu/kt-datacards) 进行中文资源适配，卡面主要来自 Warhammer Community 发布的官方简体中文规则 PDF。

## 功能

- 使用中文队伍名称或英文队伍标识搜索队伍。
- 在游戏内生成队伍卡盒，保留取牌、**Place** 摆放和 **Recall** 回收功能。
- 在线加载卡牌图片与模型资源，支持在联机房间中使用。
- 提供 Windows 安装脚本，普通玩家无需安装 Python 或运行抓取程序。

这是规则卡牌与卡盒资源项目，不负责生成完整的战棋模型队伍。卡盒外观、卡背、标记及部分按钮和自动属性沿用原模板，部分文字仍为英文。

## 下载与安装（Windows）

使用前需要已安装 Tabletop Simulator，并能访问 GitHub 的原始资源域名 `raw.githubusercontent.com`。

1. 在仓库首页点击 **Code → Download ZIP**，下载后完整解压。资源包约 535 MiB，下载可能需要一些时间。
2. 打开解压后的文件夹，双击 **Install.cmd**。
3. 脚本会将中文生成器和死亡天使示例卡盒复制到 Windows“文档”目录下的：

   ```text
   My Games\Tabletop Simulator\Saves\Saved Objects\KT Chinese GitHub
   ```

安装完成后即可进入游戏。示例卡盒仅提供死亡天使，**中文生成器可选择全部 48 个队伍**。

也可以手动安装：将仓库 `SavedObjects` 文件夹中的两个 JSON 文件复制到上述目录；目标目录不存在时可自行创建。

## 游戏内使用

1. 进入 TTS 房间，打开 **Objects（对象）→ Saved Objects（已保存物品）→ KT Chinese GitHub**。
2. 将 **Kill Team 中文生成器**放到桌面。
3. 点击“生成队伍”，搜索或选择队伍，等待对应卡盒加载。
4. 点击卡盒上的 **Place** 摆放牌组，或直接从盒中取出物品；点击 **Recall** 回收。
5. 鼠标放在卡牌上，按 **F** 翻面，按住 **Alt** 放大查看。

联机时，加入房间的玩家会加载同一批在线资源，无需运行 Python 或抓取脚本；每位玩家均需能访问资源地址。

## 常见问题

**卡牌只有阵营图标，没有规则文字？**

通常是卡背朝上。先将鼠标放在卡牌上按 F 翻面。

**队伍列表没有更新，或只看到死亡天使？**

确认使用的是中文生成器，而非死亡天使示例卡盒。更新安装后，重新从已保存物品中放置生成器；桌上已有的旧生成器可能仍保留旧列表。也可重新载入房间。

**图片空白、模型加载失败或队伍菜单无法打开？**

首次加载需要下载资源，请稍候。如果持续失败，检查是否能在浏览器中打开[在线队伍目录](https://raw.githubusercontent.com/megumi678/kt-datacards-cn/main/output/team-urls.json)。反馈问题时请附上队伍名称、报错文字和截图。

**是否会自动获取最新官方规则？**

游戏加载的是本仓库已发布的资源，不会现场抓取官网 PDF。官方规则更新后，需要重新构建并发布资源；卡牌内容应结合所使用的规则版本核对。

## 卡牌来源与适配说明

- 主要卡面来自[官方 Kill Team 下载页](https://www.warhammer-community.com/en-gb/downloads/kill-team/)中的简体中文 PDF。
- 强征小队的独立选人卡由同一官方中文 PDF 的附录整理而成。
- 执政官之手的大享乐者卡在本次使用的官方中文 PDF 中缺失，因此提供基于原模板英文卡的**非官方中文补译**，卡面已明确标注，数值沿用原模板。
- 自动属性沿用原模板，未随中文卡面重新解析；若与卡面不同，请核对当前使用的规则版本。

本项目已进行游戏内使用测试，以及资源引用、Lua 语法、图片解码和 48 队生成流程的模拟检查。这不代表每张卡牌均已逐一核对；构建时的检查记录见 [validation.json](validation.json)。

## 项目结构

| 路径 | 用途 |
| --- | --- |
| `output/` | 游戏在线加载的队伍目录、卡盒 JSON、图片和模型 |
| `SavedObjects/` | 可导入 TTS 的生成器和示例卡盒 |
| `Install.cmd`、`Install-SavedObjects.ps1` | Windows 安装入口与脚本 |
| `source-patches/` | 相对于原项目的代码补丁、固定来源映射和补充 PDF |
| [teams.csv](teams.csv) | 队伍中文名称、英文标识与卡牌数量 |
| `deployment.json`、`validation.json` | 构建配置与检查记录 |
| `files.sha256` | 文件校验清单 |

## 开发与维护

处理流程为：获取官方中文 PDF → 裁剪与映射卡面 → 生成 TTS 卡牌和卡盒资源 → 发布到 GitHub → 游戏内加载。

`source-patches` 是原项目的覆盖补丁，不是完整的独立源码项目。重新构建需要原项目环境、补丁及映射所对应的中文裁剪 PDF。构建入口为 `tools/build_chinese_all.py`，可通过 `--output` 指定输出目录，通过 `--base-url` 指定资源地址。

构建器会核对固定的 PDF 哈希。源文件更新后需重新核对卡面布局与映射，不能直接沿用旧映射。自行部署时应同时修改生成器及卡盒资源引用，保持 `output/` 的目录结构。

## 致谢与反馈

感谢 [Wen-Qualtu/kt-datacards](https://github.com/Wen-Qualtu/kt-datacards) 提供原始工具与模板，以及 Warhammer Community 提供规则资料。本项目是社区中文适配，与 Games Workshop 无隶属关系；原项目代码及规则、美术资源的权利归各自权利人所有。

如发现卡面错配、缺失或加载问题，请在 [Issues](https://github.com/megumi678/kt-datacards-cn/issues) 提交队伍名称、卡牌名称、复现步骤与截图。
