# Surge Tools

一个用于合并和管理 Surge 规则和模块的工具。

## 功能特点

- 规则合并
  - 支持多个规则源的合并
  - 自动去重和排序
  - 支持规则优先级配置
  - 支持排除特定规则和规则集
  - 自动生成规则统计信息

- 模块合并
  - 支持多个模块源的合并
  - 自动合并 MITM hostname
  - 支持排除特定段落和行
  - 支持段落优先级配置
  - 支持从模块提取规则
  - 保持注释和格式

- 自动化
  - 通过 GitHub Actions 自动更新
  - 定时拉取最新规则和模块
  - 自动生成更新时间戳
  - 失败自动重试

- 配置灵活
  - 支持 YAML 配置文件
  - 可自定义输出目录
  - 可配置规则类型优先级
  - 可配置段落排序
  - 详细的日志输出

## 目录结构

```
surge-tools/
├── .github/
│   └── workflows/
│       └── update-rules.yml
├── rules/
├── modules/
├── config/
│   └── config.yaml
├── src/
│   └── main.py
└── README.md
```



## 特别声明

1. 本项目内所有资源文件，禁止任何公众号、自媒体进行任何形式的转载、发布。
2. 编写本项目主要目的为学习和研究ES6，无法保证项目内容的合法性、准确性、完整性和有效性。
3. 本项目涉及的数据由使用的个人或组织自行填写，本项目不对数据内容负责，包括但不限于数据的真实性、准确性、合法性。使用本项目所造成的一切后果，与本项目的所有贡献者无关，由使用的个人或组织完全承担。
4. 本项目中涉及的第三方硬件、软件等，与本项目没有任何直接或间接的关系。本项目仅对部署和使用过程进行客观描述，不代表支持使用任何第三方硬件、软件。使用任何第三方硬件、软件，所造成的一切后果由使用的个人或组织承担，与本项目无关。
5. 本项目中所有内容只供学习和研究使用，不得将本项目中任何内容用于违反国家/地区/组织等的法律法规或相关规定的其他用途。
6. 所有基于本项目源代码，进行的任何修改，为其他个人或组织的自发行为，与本项目没有任何直接或间接的关系，所造成的一切后果亦与本项目无关。
7. 所有直接或间接使用本项目的个人和组织，应24小时内完成学习和研究，并及时删除本项目中的所有内容。如对本项目的功能有需求，应自行开发相关功能。
8. 本项目保留随时对免责声明进行补充或更改的权利，直接或间接使用本项目内容的个人或组织，视为接受本项目的特别声明。



## Surge官网及TG社区

[Surge官网](https://nssurge.com/)

[Surge社区1](https://t.me/SurgeCommunity)

[Surge社区2](https://t.me/loveapps)

## surge配置

开发者推荐最小配置👇👇👇👇

https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf

Lucky配置 👇👇👇👇

https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf

深巷有喵配置 👇👇👇👇

https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf



## 模块查找

https://surge.qingr.moe

[Yfamily - iOS 代理工具配置与教程（Surge、Shadowrocket、小火箭、QuantumultX、Loon 等](https://whatshub.top/)

https://github.com/Rabbit-Spec/Surge/tree/Master/Module



## 必装模块

[BoxJs](https://github.com/chavyleung/scripts/raw/master/box/rewrite/boxjs.rewrite.surge.sgmodule)

[ScriptHub](https://raw.githubusercontent.com/Script-Hub-Org/Script-Hub/main/modules/script-hub.surge.sgmodule)

[SubStore](https://raw.githubusercontent.com/sub-store-org/Sub-Store/master/config/Surge-Beta.sgmodule)

[三个模块教程](https://mylucky.cyou/post/20240107003508.html)



## 规则集查找(blackmatrix7大佬的)

分流规则

https://github.com/blackmatrix7/ios_rule_script/tree/master/rule

复写规则

https://github.com/blackmatrix7/ios_rule_script/tree/master/rewrite



## Loon插件及模块,配合ScriptHub使用

[luestr/ProxyResource: 可莉的Loon资源库 | 插件 | 脚本 | 规则](https://github.com/luestr/ProxyResource)

[fmz200/wool_scripts: 收集一些QuantumultX、Loon、Surge、ShadowRocket的配置与去广告规则。](https://github.com/fmz200/wool_scripts)



## 以下排名不分先后

[@ddgksf2013](https://github.com/ddgksf2013)[*@Blackmatrix7*](https://github.com/blackmatrix7/ios_rule_script) [*@DivineEngine*](https://github.com/DivineEngine) [*@App2smile*](https://github.com/app2smile/rules)  [*@Peng-YM*](https://github.com/Peng-YM) [*@Nick-workflow*](https://github.com/Nick-workflow) [*@KOP-XIAO*](https://github.com/KOP-XIAO) [*@NobyDa*](https://github.com/NobyDa) [*@Neurogram-R*](https://github.com/Neurogram-R) [*@yjqiang*](https://github.com/yjqiang) [*@O7Y0*](https://github.com/O7Y0) [*@Choler*](https://github.com/Choler) [*@id77*](https://github.com/id77) [*@zmqcherish*](https://github.com/zmqcherish) [*@Qure*](https://github.com/Koolson/Qure) [*@Orz-3*](https://github.com/Orz-3) [*@kyle*](https://github.com/Xirou) [*@HotKids*](https://github.com/hotKids) [*@langkach*](https://github.com/langkhach270389) [*@lxk0301*](https://github.com/lxk0301) [*@zqzess*](https://github.com/zqzess/rule_for_quantumultX) [*@Anti-AD*](https://github.com/privacy-protection-tools/anti-AD) [*@VirgilClyne*](https://github.com/VirgilClyne/iRingo#iringo) [*@zZPiglet*](https://github.com/zZPiglet/Task/tree/master) [*@Chavyleung*](https://github.com/chavyleung) [luestr]([luestr/ProxyResource: 可莉的Loon资源库 | 插件 | 脚本 | 规则](https://github.com/luestr/ProxyResource)) [fmz200/]([fmz200/wool_scripts: 收集一些QuantumultX、Loon、Surge、ShadowRocket的配置与去广告规则。](https://github.com/fmz200/wool_scripts))