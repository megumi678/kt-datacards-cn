# Kill Team 中文卡牌（死亡天使）

基于 [Wen-Qualtu/kt-datacards](https://github.com/Wen-Qualtu/kt-datacards) 的 TTS 中文卡面部署包。
官方中文 PDF 来源：[Warhammer Community](https://www.warhammer-community.com/en-gb/downloads/kill-team/)。

本版保留原卡盒的取牌、摆放和回收脚本，将死亡天使的 25 张卡替换为官方中文正反面，共 31 个内容面。
自动属性、内部标识及部分界面仍保留原英文数据。其他队伍尚未加入。

## 使用

1. 通过本仓库 Code → Download ZIP 下载并解压。
2. Windows 用户双击 `Install.cmd`，安装生成器和卡盒到 TTS 的 Saved Objects 独立子目录。
3. 在 TTS 中打开 Objects → Saved Objects → KT Chinese GitHub。
4. 拖出中文生成器，点击“生成队伍”，选择“死亡天使”。
5. 从生成的卡盒中取牌，按 Alt 检查中文卡面。也可直接拖出中文卡盒测试。

图片和 JSON 直接从本仓库的 `main` 分支加载，无需启动本机 HTTP 服务。
必须上传下面的 `output/` 目录及其子目录，不能仅上传 ZIP 文件或生成器 JSON。
如果默认分支不是 `main`，需要重新配置所有资源地址。

## 目录

- `output/`：游戏读取的队伍索引、卡盒 JSON、模型、贴图及数据。
- `SavedObjects/`：带 ObjectStates 包装的 TTS 已保存对象，供玩家安装。
- `config/`（如有）：资源引用需要的原脚本。
- `source-patches/`：相对原项目的代码修改文件，覆盖到原始完整项目对应位置使用；不是独立的全量源码。
- `deployment.json`：仓库和资源地址配置。

## 验证与排错

部署前已检查中文卡面映射、JSON、Lua 语法及本地资源文件。
实际游戏里曾出现本机 HTTP 模型/贴图加载失败；本版本改用 GitHub HTTPS，仍需上传后进行游戏内验证。

先在浏览器打开以下地址，应显示 JSON 内容而不是 404 或登录页面：

https://raw.githubusercontent.com/megumi678/kt-datacards-cn/main/output/team-urls.json

如果失败，检查：仓库是否 Public、分支是否 main、output 是否位于仓库根目录。
若浏览器正常而 TTS 仍加载失败，检查游戏能否访问 raw.githubusercontent.com，并保留具体错误网址。
更新后重新从 Saved Objects 拖出新生成器；桌上旧物品不会自动替换脚本。
请勿继续使用之前的 KT Chinese Local 物品。

原始图片及游戏内容属于其相应权利人；本仓库未对第三方作品另行授予许可。
