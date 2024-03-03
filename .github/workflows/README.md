# Github 工作流

## 多语言编译
配置文件 workflows/locale-po.yml

修改多语言时，应使用 dev_locale 分支

## 打包发布
配置文件 publish-release.yml

注意 checkout时不能使用 fetch-depth 参数，因为后续要使用 git log 获取文件修改时间。

