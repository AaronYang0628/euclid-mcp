# DevContainer 多项目开发环境

这个devcontainer配置支持在同一个容器中开发多个使用不同Python版本的子项目。

## 特性

- ✅ 使用 pyenv 管理多个 Python 版本（预装 3.9, 3.10, 3.11, 3.12）
- ✅ 支持多种依赖管理工具（pip, poetry, pipenv, uv）
- ✅ 预配置 VS Code Python 开发环境
- ✅ 包含常用开发工具（black, ruff, mypy, pytest等）
- ✅ 预装 OpenCode CLI / Claude Code CLI / MCP Inspector
- ✅ 预装 `kubectl`（可直接连接本地/远程 Kubernetes 集群）
- ✅ Git 和 SSH 配置

## 使用方法

### 1. 打开容器

在 VS Code 中：
1. 安装 "Dev Containers" 扩展
2. 按 `F1` 或 `Ctrl+Shift+P`
3. 选择 "Dev Containers: Reopen in Container"

### 2. 为子项目设置 Python 版本

```bash
# 进入子项目目录
cd project1

# 设置该项目使用的 Python 版本
pyenv local 3.11.7

# 这会创建 .python-version 文件，pyenv 会自动识别
```

### 3. 创建虚拟环境

#### 使用 venv（标准库）
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 使用 Poetry
```bash
poetry init  # 初始化新项目
poetry install  # 安装依赖
poetry shell  # 激活虚拟环境
```

#### 使用 Pipenv
```bash
pipenv install  # 创建虚拟环境并安装依赖
pipenv shell  # 激活虚拟环境
```

### 4. 项目结构示例

```
euclid-mcp/
├── .devcontainer/
│   ├── devcontainer.json
│   ├── setup.sh
│   └── README.md
├── project1/              # Python 3.11 项目
│   ├── .python-version    # 内容: 3.11.7
│   ├── .venv/
│   ├── pyproject.toml
│   └── src/
├── project2/              # Python 3.12 项目
│   ├── .python-version    # 内容: 3.12.1
│   ├── .venv/
│   ├── requirements.txt
│   └── app/
└── project3/              # Python 3.9 项目
    ├── .python-version    # 内容: 3.9.18
    ├── Pipfile
    └── main.py
```

## 常用命令

### Claude Code 命令

```bash
# 启动 Claude Code（需要先配置 API key）
claude

# 配置 API key
claude config set apiKey YOUR_API_KEY

# 查看帮助
claude --help

# 在特定目录启动
cd project1
claude
```

### OpenCode 命令

```bash
# 检查版本
opencode --version

# 建议在项目根目录启动
cd /workspace/euclid-mcp

# 查看配置
opencode debug config

# 查看 MCP
opencode mcp list

# 启动 Web
opencode web --port 7788
```

### Kubernetes 命令

```bash
# 检查 kubectl 是否可用
kubectl version --client

# 查看当前上下文
kubectl config current-context
```

说明：

- `AI_MODEL_KEY` 通过 devcontainer `containerEnv` 预留，重建后请在容器内设置真实值。
- 若内网证书链不完整，已默认设置 `NODE_TLS_REJECT_UNAUTHORIZED=0` 便于本地调试。

### Pyenv 命令

```bash
# 查看已安装的 Python 版本
pyenv versions

# 安装新的 Python 版本
pyenv install 3.13.0

# 查看可安装的版本
pyenv install --list

# 设置全局默认版本
pyenv global 3.12.1

# 设置当前目录的版本（创建 .python-version）
pyenv local 3.11.7

# 设置当前 shell 会话的版本
pyenv shell 3.10.13

# 创建虚拟环境
pyenv virtualenv 3.11.7 myproject-env

# 激活虚拟环境
pyenv activate myproject-env

# 停用虚拟环境
pyenv deactivate
```

### VS Code Python 解释器选择

1. 按 `Ctrl+Shift+P`
2. 输入 "Python: Select Interpreter"
3. 选择对应项目的虚拟环境

## 添加新的 Python 版本

如果需要其他 Python 版本：

```bash
# 安装特定版本
pyenv install 3.8.18

# 或安装最新的补丁版本
pyenv install 3.13
```

## 依赖管理工具对比

| 工具 | 适用场景 | 配置文件 |
|------|---------|---------|
| **venv + pip** | 简单项目，标准库 | requirements.txt |
| **Poetry** | 现代项目，依赖解析 | pyproject.toml |
| **Pipenv** | 自动虚拟环境管理 | Pipfile |
| **uv** | 超快速安装（Rust实现） | requirements.txt |

## 故障排除

### Python 版本未切换

```bash
# 确保 pyenv 已初始化
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# 重新加载 shell 配置
source ~/.bashrc  # 或 source ~/.zshrc
```

### VS Code 未识别虚拟环境

1. 重新加载窗口：`Ctrl+Shift+P` → "Developer: Reload Window"
2. 手动选择解释器：`Ctrl+Shift+P` → "Python: Select Interpreter"

### 安装 Python 版本失败

```bash
# 安装构建依赖
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

## 自定义配置

### 修改预装的 Python 版本

编辑 `.devcontainer/setup.sh`，修改这些行：

```bash
pyenv install 3.9.18 || true
pyenv install 3.10.13 || true
# 添加或删除版本...
```

### 添加更多 VS Code 扩展

编辑 `.devcontainer/devcontainer.json` 的 `extensions` 数组。

### 修改默认 Python 版本

编辑 `.devcontainer/setup.sh`：

```bash
pyenv global 3.12.1  # 改为你想要的版本
```
