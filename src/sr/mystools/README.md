# 代码来源

https://github.com/Ljzd-PRO/nonebot-plugin-mystool 2024-05-16复制

# 适配改动

- 复制 `command` 中的 `login.py` 和 `plan.py`
- 删除所有nonebot相关代码 
- 修改 `model/config.py` 中的 `root_path`，指向项目 `config/mystool2` 文件夹 
- 修改 `model/common.py` 中的 `StarRailNote`，增加委托类 `StarRailNoteExpedition`
- 修改 `utils/common.py` 中的 `generate_qr_img` 直接返回二维码图片
- 修改 `utils/common.py` 中的 `logger` 指向 `log_utils.log`