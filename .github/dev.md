# 1.开发环境

## 1.1.Python

推荐使用 [3.11.9](https://www.python.org/downloads/release/python-3119/)

## 1.2.虚拟环境

普通运行

```shell
pip install -r requirements-dev.txt
```

开发额外

```shell
pip install -r requirements-dev-ext.txt
```

生成最终使用

```shell
pip-compile --annotation-style=line --index-url=https://pypi.tuna.tsinghua.edu.cn/simple --output-file=requirements-prod.txt requirements-dev.txt
```

# 2.打包

## 2.1.安装器

生成spec文件

```shell

```