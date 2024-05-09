# Honkai Star Rail - One Dragon
__崩坏：星穹铁道 - 一条龙__ - 基于图像识别的自动游戏脚本，适用于PC端。

本脚本的终极目标是可以让你在日常```忘掉```这个游戏，做到完全的托管。

目前支持`锄大地`、`体力刷本`、`逐光捡金`、`模拟宇宙`等日常功能。下载、运行及使用方式，见 [wiki](https://github.com/DoctorReid/StarRailAutoProxy/wiki)，或conda+powershell方式见[install](#install)。

如果喜欢本项目，可右上角送作者一个```Star```

如有疑问，可以提ISSUE或进QQ群```743525216```咨询。~~__(虽然上班搬砖时间回复较慢，下班写代码时间也回复较慢__~~

## 项目进度

- [锄大地](https://github.com/DoctorReid/StarRailOneDragon/wiki/%E5%8A%9F%E8%83%BD_%E9%94%84%E5%A4%A7%E5%9C%B0) `2.1 已完成` (不包含3D地图) 支持`黄泉`秘技
- [日常](https://github.com/DoctorReid/StarRailOneDragon/wiki/%E5%8A%9F%E8%83%BD_%E6%97%A5%E5%B8%B8) `已完成`
- [模拟宇宙](https://github.com/DoctorReid/StarRailOneDragon/wiki/%E5%8A%9F%E8%83%BD_%E6%A8%A1%E6%8B%9F%E5%AE%87%E5%AE%99) `已完成` 第九宇宙测试中 支持`黄泉`秘技
- [逐光捡金](https://github.com/DoctorReid/StarRailOneDragon/wiki/%E5%8A%9F%E8%83%BD_%E9%80%90%E5%85%89%E6%8D%A1%E9%87%91) `已完成`

![APP主页](https://github.com/DoctorReid/StarRailOneDragon/blob/main/.github/wiki/app.png)

[当前进度](https://github.com/DoctorReid/StarRailOneDragon/milestone/8)

## 源码相关

### 安装

#### conda+powershell

```powershell
git clone git@github.com:DoctorReid/StarRailOneDragon.git
cd StarRailOneDragon
conda create --prefix="./.env" python=3.11
conda activate ./.env
pip install -r requirements.txt
$env:PYTHONPATH="src"
python src/gui/app.py
```

## 免责声明
本软件是一个外部工具旨在自动化崩坏星轨的游戏玩法。它被设计成仅通过现有用户界面与游戏交互,并遵守相关法律法规。该软件包旨在提供简化和用户通过功能与游戏交互,并且它不打算以任何方式破坏游戏平衡或提供任何不公平的优势。该软件包不会以任何方式修改任何游戏文件或游戏代码。

This software is open source, free of charge and for learning and exchange purposes only. The developer team has the final right to interpret this project. All problems arising from the use of this software are not related to this project and the developer team. If you encounter a merchant using this software to practice on your behalf and charging for it, it may be the cost of equipment and time, etc. The problems and consequences arising from this software have nothing to do with it.

本软件开源、免费，仅供学习交流使用。开发者团队拥有本项目的最终解释权。使用本软件产生的所有问题与本项目与开发者团队无关。若您遇到商家使用本软件进行代练并收费，可能是设备与时间等费用，产生的问题及后果与本软件无关。


请注意，根据MiHoYo的 [崩坏:星穹铁道的公平游戏宣言]([https://hsr.hoyoverse.com/en-us/news/111244](https://sr.mihoyo.com/news/111246?nav=news&type=notice)):

    "严禁使用外挂、加速器、脚本或其他破坏游戏公平性的第三方工具。"
    "一经发现，米哈游（下亦称“我们”）将视违规严重程度及违规次数，采取扣除违规收益、冻结游戏账号、永久封禁游戏账号等措施。"

## 相关项目
点赞以下灵感来源
- [崩坏：星穹铁道 模拟宇宙自动化](https://github.com/CHNZYX/Auto_Simulated_Universe)
- [崩铁速溶茶](https://github.com/LmeSzinc/StarRailCopilot)
- [崩坏：星穹铁道自动锄大地](https://github.com/Starry-Wind/StarRailAssistant)
