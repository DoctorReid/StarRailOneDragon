# 代码来源

https://github.com/Ljzd-PRO/nonebot-plugin-mystool 2024-05-16复制

# 适配改动

1. 删除了 `command`, `utils/good_image.py`, `model/upgrade`
2. 删除 `nonebot` 相关代码
3. 全局替换 logger
   - `from nonebot.log import logger` -> `from basic.log_utils import log`
   - `logger.info` -> `log.info`
   - `logger.warning` -> `log.warning`
   - `logger.error` -> `log.error`
   - `logger.exception` -> `log.exception`
   - `logger.debug` -> `log.debug`
   - `logger.success` -> `log.info`
   - 删除剩余出现logger的地方
4. 修改 `model/config.py` 中的 `root_path`，指向项目 `config/mystool2` 文件夹
5. 修改 `model/common.py` 中的 `StarRailNote`，增加委托类 `StarRailNoteExpedition`
6. 复制原项目中的 `command/login.py` 里的 `phone` 命令，用于获取验证码。转化成代码 `get_device_id_and_try_captcha`
   - 删除了自动验证码部分
7. 复制原项目中的 `command/login.py` 里的 `captcha` 命令，用于输入验证码后验证。转化成代码 `do_login`，并在生成账号时初始化 `mission_games` 字段。
8. 复制原项目中的 `command/plan.py` 里的 `perform_game_sign` 命令，修改删除发送消息部分，用于游戏签到。
   - 修改 account 限制为当前手机号用户
9. 复制原项目中的 `command/plan.py` 里的 `perform_bbs_sign` 命令，修改删除发送消息部分，用于游戏签到。
   - 修改 account 限制为当前手机号用户
10. 解决 `pydantic` 版本冲突
   - 修改`BaseSettings`的引用，从 `pydantic` 迁移到 `pydantic_settings`
   - 删除 `class Config(Preference.Config)`
   - 删除 `json_encoders = UserAccount.Config.json_encoders`
   - `.json()` -> `.model_dump_json()`
   - `.dict()` -> `.model_dump()`
   - 查找 `Optional[` 的类型声明，添加默认值
   - 运行时修复部分缺失的默认值和缺失的类型声明

# 适配改动

- 复制 `command` 中的 `login.py` 和 `plan.py`
- 删除所有nonebot相关代码 
- 修改 `model/config.py` 中的 `root_path`，指向项目 `config/mystool2` 文件夹 
- 修改 `model/common.py` 中的 `StarRailNote`，增加委托类 `StarRailNoteExpedition`
- 修改 `utils/common.py` 中的 `generate_qr_img` 直接返回二维码图片