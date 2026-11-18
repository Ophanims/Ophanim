# Ophanim

本地运行的卫星仿真 Webapp。Python + Skyfield 按仿真步实时计算，通过 WebSocket 展示；完整回放和分类分析数据保存到 PostgreSQL + TimescaleDB。项目与模型保存在 `data/ophanim/`。不需要整段预加载，也不启动 MySQL。

## 安装与运行

需要 Python 3.12、兼容当前 Next.js 的 Node.js 和 npm。使用本机数据库时还需要运行中的 Docker Desktop；也可以连接已有 TimescaleDB。

```bash
# 首次安装：API、物理与几何仿真
./setup.sh
# 可选：基线算法、PPO、训练与评估
./setup.sh --ml
```

首次使用在 `.env` 设置 `DB_USER`、`DB_PASSWORD`、`DB_NAME`，可参考 `.env.example`，不要覆盖已有凭据。默认数据库端口为 15432，可通过 `DB_PORT` 修改。已有 TimescaleDB 则设置 `DATABASE_URL`，启动脚本将直接连接，不创建本地容器。

```bash
./start.sh
```

脚本先连接数据库；本机数据库未运行时通过 `compose.records.yml` 启动专用 TimescaleDB，再构建并启动前后端。后端会初始化独立的 `ophanim` schema，保留旧库表。数据库不可用时明确失败，不会悄悄改用文件记录。

打开脚本打印的首页地址，默认前端端口 3000。按 **Ctrl+C** 或执行 `./stop.sh` 停止前后端。数据库保持运行；需要停止它时执行：

```bash
docker compose -f compose.records.yml stop
```

不删除容器卷或数据库目录。前后端支持 `BACKEND_PORT`、`FRONTEND_PORT`，也可使用 `./start.sh --backend-port 8001 --frontend-port 3000`。`SIMULATION_PUSH_INTERVAL_S` 默认 0.1 秒，仅控制展示通知频率；算法步长、完整记录与渲染帧率分别处理。

## 记录、回放与分析

所有新记录写入 TimescaleDB：`ophanim.records` 保存项目、算法、随机种子所在的完整配置、代码哈希与状态；`simulation_frames` 保存与实时展示同源的完整快照。分析表按类型共享，通过 `record_id`、`id` 和仿真 `time` 区分每次运行与具体实体：

- `satellite_states`、`station_states`：卫星与基站状态。
- `task_states`、`mission_states`：保留两种任务模型的原始语义。
- `link_states`：按 `type`、`src`、`dst` 区分链路。
- `network_metrics`：节点数、链路数、任务数、奖励与平均电量。

后台有界队列批量提交，每一步都记录，展示允许跳帧。结束状态在最终批次提交后发送。`data/ophanim/record_recovery/` 中的临时 NDJSON 日志在成功提交后移除，写入失败时保留，以便恢复。仿真时间用于回放与分析；实际创建时间独立保存在记录元数据中。没有默认删除历史的保留策略。

工作区导航栏的 **Record** 打开当前项目的记录列表；选择 **Replay** 直接读取历史快照，并显示播放、暂停和进度拖动控制。回放采用记录中的项目配置；**Return to live workspace** 返回当前项目。记录列表接口支持 `project_id` 筛选。

回放仍使用 `/api/records/{record_id}?start_frame=0&frame_limit=600`。下载接口流式导出 NDJSON。分类分析示例：

```text
/api/records/{record_id}/analysis?entity_type=satellites&id=sat_0&start_frame=0&frame_limit=600
```

`id` 可选；链路查询中的 `id` 匹配任意端点。返回最多 `point_limit` 个点（默认 5000，最大 10000）；使用 `next_start_point` 继续读取同一帧窗口。可直接通过 SQL 对分析表中的电量、任务进度、速率等列聚合。

已有的文件记录继续可读，也可以导入数据库。导入可重复执行，不重复计数，源文件保留：

```bash
.venv/bin/python scripts/import_record_files.py
# 写入失败或异常退出后的记录恢复
.venv/bin/python scripts/import_record_files.py --recovery
```

## 数据备份与旧库

数据库默认保存在 `data/timescale/`，应使用 PostgreSQL 的备份方式；复制数据库目录前应先正常停止数据库。同时备份 `data/ophanim/` 可保留项目、模型、旧文件记录和恢复日志。原 `data/mysql/`、`data/postgres/`、旧轨道缓存目录保留，运行时不再读取轨道缓存。

旧 MySQL/Timescale v0 数据迁移仍由显式命令执行；完成后可通过上面的文件导入命令写入新记录库：

```bash
.venv/bin/python -m pip install -r backend/requirements-legacy.txt
.venv/bin/python scripts/migrate_legacy_data.py
.venv/bin/python scripts/import_record_files.py
```

原 Docker 配置归档于 `docs/legacy-docker/`，新运行方式只启动 `compose.records.yml` 中的记录数据库。

## 验证

```bash
.venv/bin/python scripts/generate_contracts.py --check
.venv/bin/python scripts/check_coding_rules.py
PYTHONPATH=backend MPLCONFIGDIR=/private/tmp/ophanim-mpl .venv/bin/python -m unittest discover -s backend/tests -v
# 使用配置的真实 TimescaleDB，在临时 schema 中验证 SQL、回放、分析与级联删除
.venv/bin/python scripts/test_record_database.py
```

前端执行 `npm --prefix frontend run check:rules`、`npm --prefix frontend run build`。浏览器测试需要运行中的前后端与本机 Chrome。

详细功能：[合并说明](docs/SCOPE_MERGE.md)。编码规范：[通用编码法则](CODING_RULES.md)。
