# FEFKNCQ

给 AI agent 用的 skill：把你的 OC 角色做成 [STOMPGAME](https://ikkimikka.net/stompgame/)
（`?character=custom`）能直接导入的自定义角色图 `custom.png`，同时产出可设置角色名、
描述与结算评级的 `custom.zip`，并自动开始游戏。

仓库：<https://github.com/ikkimikka/FEFKNCQ>


## 合规

- 本项目为非官方第三方 skill，与游戏作者 ikkimikka 无关联。
- 仓库**不打包**作者的 `generic.png`，运行时从官方地址下载；出处与 SHA256 见
  `references/upstream.md`。
- **分发请用 GitHub 仓库 / zipball**：不要用 skill-creator 的 `package_skill.py` 直接打包
  当前工作目录，它会把 `.git/`、`__pycache__/` 以及含上游像素的本地标注图
  `numbered_map.png` 一起打进 zip。含像素产物（`custom.png`、`custom.zip`、标注图）一律
  不提交、输出到仓库外（`.gitignore` 已覆盖常见文件名）。
- OC 素材需由用户自行确认使用权；生成内容请遵守所用生图服务与上游站点条款。
- 游戏为"巨人踩踏小人"的卡通玩法，公开分享时请自行标注受众。

## 自然腿型与鞋子动作

可选 `--motion natural`：以大腿—膝盖—小腿—脚踝的完整连接生成六帧动作，保持鞋型。默认等比完整保留轮廓，避免顶部裁掉膝盖；比例不合适时重画素材。缺图会在输出前明确报错。缺少上半身服装参考时默认 JK 制服，已有服装与鞋袜保持原设定。参见 [自然步态说明](references/natural-motion.md) 与 [解剖及服装规则](references/anatomy-and-outfit.md)。

回归检查：`python -B -m unittest discover -s tests -v`。

## 来源

基于 [iKKiMiKKA/FEFKNCQ](https://github.com/ikkimikka/FEFKNCQ) 的 `48e6573` 版本，增加自然人腿及穿鞋动作模式、合成比例控制和回归测试。此仓库保留原始安装入口：技能位于仓库根目录，内部名称仍为 `stompgama`。
