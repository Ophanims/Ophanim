# Ophanim

本地运行的卫星仿真 Webapp。访问首页，点击 **Get Started** 展开项目管理；项目、记录、模型和缓存保存在 `data/ophanim/`，运行不需要 Docker、MySQL 或 PostgreSQL。

## 安装与运行

需要 Python 3.12、兼容当前 Next.js 的 Node.js 和 npm。

```bash
# 首次安装：API、物理与几何仿真
./setup.sh

# 需要基线算法、PPO、训练与评估时安装完整依赖
./setup.sh --ml

# 启动前后端；首次或代码变化时自动构建前端
./start.sh
```

脚本在前台运行，终端保留运行日志。打开脚本打印的首页地址，默认前端端口为 3000。按 **Ctrl+C** 或在另一终端执行 `./stop.sh`，同时关闭前后端和它们的子进程。

```bash
./stop.sh
.venv/bin/python scripts/run_app.py status

# 可选：覆盖端口
./start.sh --backend-port 8001 --frontend-port 3000
```

`.env` 中的 `BACKEND_PORT`、`FRONTEND_PORT` 仍然有效。脚本统一设置前端 API 地址，并在构建缓存中记录该地址；端口或前端源码变化时自动重新构建。日常使用生产模式，不启动自动重载、容器、数据库或数据库管理页面。

## 数据与迁移

备份 `data/ophanim/` 即可保留日常使用的项目、记录与模型。原来的 `data/mysql/`、`data/postgres/` 等数据库目录保留，不会被启动或停止脚本删除。

旧数据库迁移只在显式运行下面命令时执行，需要可访问的旧数据库和 `.env` 中的旧连接配置：

```bash
.venv/bin/python -m pip install -r backend/requirements-legacy.txt
.venv/bin/python scripts/migrate_legacy_data.py
```

原 Docker 配置归档于 `docs/legacy-docker/`，仅供查阅；其相对路径仍以原仓库位置为基准，不能直接在归档目录中启动。Docker 软件、镜像及数据库文件没有卸载或删除。

详细功能：[合并说明](docs/SCOPE_MERGE.md)。编码规范：[通用编码法则](CODING_RULES.md)。
