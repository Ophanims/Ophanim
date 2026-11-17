# 两个 Webapp 的统一合并

## 最终使用方式

Ophanim 与 SCOPE 已合为一个 Next.js Webapp 和一个 FastAPI 服务。所有项目进入同一个列表，使用同一份配置、同一个工作区、同一套运行控制与记录回放。原 SCOPE 目录只作为迁移来源，运行时不依赖它。

| 功能 | 统一入口 |
| --- | --- |
| 应用标题、简介与开始入口 | `/` |
| 同页项目列表、创建、编辑、删除 | `/#projects`，原 `/dashboard` 自动跳转 |
| 项目工作区 | `/workspace/{project_id}` |
| 记录列表、下载、删除 | `/records` |
| 记录回放 | `/workspace/{project_id}?record_id={record_id}` |
| HTTP API | `/api/projects`、`/api/cache/*`、`/api/jobs/*`、`/api/records` |
| WebSocket | `/api/simulation/ws` |

工作区选择运行方式：Ophanim Physics、Geometry、L2D2、PHOENIX、MHSPO、PPO。它们是同一会话服务中的策略，使用共同的 `Project` 输入与 `SimulationSnapshot` 输出。两种 PHOENIX 实现的调度模型不同：Ophanim Physics 保留原物理任务模型中的调度策略，PHOENIX 选项运行迁入的基线环境。

Universe、Geometry、Object、Map、参数与数据流视图、分屏、配置、训练和评估都在统一工作区内。原来的仿真和记录 URL 重定向到此工作区。

首页与项目管理共用同一个地球场景。首次进入时先显示加载页，只有纹理加载并完成地球首帧渲染后才展示内容；点击 Get Started 原地展开项目管理，切换时不重建背景。背景加载失败时可重试，项目列表按需加载。

## 项目和记录

- 原 MySQL 项目启动时自动迁入统一项目目录，数字 ID 保留为字符串，不创建另一份带前缀的项目副本。
- SCOPE 已迁入的项目与原有项目并列显示。修改、删除和运行都通过同一个 API。
- 旧名称只在有明确范围的 v0 数据适配器中接收，迁移后仅输出规范名称。GHz／MHz 转换成硬件契约的 Hz；物理引擎使用的派生单位具有明确后缀。
- 原有处理器、电池、太阳能板与静态功率参数纳入共同的 `resources` 配置，地面站保留 `altitude_m`。
- 新记录直接保存发送给页面的同一份快照，附带完整项目配置、算法、代码哈希和版本。历史回放无需依赖仍然存在的项目。
- Timescale 历史记录启动时流式转换到同一个记录目录，使用 `timescale_{旧记录ID}`。旧数据没有保存代码哈希，明确标为 `unknown-v0`；旧记录没有保存当时的地面站配置时，只能使用当前项目中的地面站信息恢复标识。
- `migrations.json` 记录已经处理的项目和记录，避免删除后重启又从旧库恢复。旧数据库内容与原 SCOPE 目录保留。

本机已迁入 SCOPE 的 1 个项目及 14 个模型／归一化文件。迁移检查未发现当前 Timescale 库中已有历史记录，历史转换路径使用构造的 v0 数据进行回归验证。

默认运行数据位于 `data/ophanim/`：

```text
projects/          # 唯一项目目录，类型化 JSON
records/           # 统一记录元数据与完整 Snapshot NDJSON
models/            # 导入检查点、按项目保存的训练版本
cache/             # 可重新计算的派生数据
output/            # 评估结果、日志、图表
migrations.json    # 一次性迁移完成标记
```

运行数据不提交到 Git；迁移到其他机器时应单独备份此目录。离线迁移 SCOPE 项目与权重：

```bash
.venv/bin/python scripts/import_scope_data.py /path/to/SCOPE --models
```

迁移工具只读取来源，拒绝覆盖内容不同的同名项目和模型。HTTP 接口不接收 pickle。

## 代码组织和编码规则

```text
backend/simulator/
  schemas/         # 唯一项目配置契约
  contracts.py     # 状态、命令和 WebSocket 消息
  core/            # 统一会话与各运行策略
  entities/        # 实体及 Snapshot
  models/          # 轨道、相机与地理计算
  env/             # 基线、PPO、训练与评估
  services/        # 项目目录、缓存、模型、记录、迁移、后台任务
  routers/         # 唯一 HTTP / WebSocket 边界
backend/core/      # 原物理内核，时钟、世界和预测缓存按会话隔离
backend/entity/    # 原物理任务模型与实体
backend/persistence/ # 数据库连接与旧数据初始化边界
frontend/src/features/simulation/
  contracts/       # 从后端生成的 TypeScript、JSON Schema、默认配置和路由
  communication/   # 所有请求、边界验证和 WebSocket 生命周期
  app/             # 项目、配置、工作区与可视化
  components/      # 展示组件与资源回收
frontend/src/app/   # 单一应用的页面和同源 API 代理
```

字段含义与单位见 [共享概念名称表](CONTRACT_NAMES.md)。遵循 [CODING_RULES.md](../CODING_RULES.md)：手写文件不超过 500 行；领域对象与快照分离；JSON 由契约模型导出；共享字段采用 `snake_case`；通信集中管理；显示与记录同源；会话独立管理时间、随机数、身份及缓存。原有两套页面、Controller 和仿真通信入口已移除。

原物理内核仍保留部分历史实现细节，例如实体内部的旧资源常量命名和算法对同一聚合内实体的引用；共享配置、公开接口、页面和记录契约已统一。规范检查不等同于对所有领域语义的形式化证明。

完整记录保存在磁盘；前端仅缓冲最近 600 帧，分页回放每次最多 600 帧。训练使用单独进程，支持查询和取消；应用关闭时回收。新训练版本保存完整后才切换项目模型指针，导入的检查点不会被覆盖。

## 本地启动

Python 使用 3.12，Node 使用兼容当前 Next.js 的版本。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/python -m pip install -r backend/requirements-ml.txt
docker compose up -d db mysql
.venv/bin/python scripts/run_backend.py --port 8001 --reload
```

另一个终端：

```bash
cd frontend
npm ci
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001 npm run dev
```

打开 `http://localhost:3000/`。启动器从根目录 `.env` 读取数据库配置，不输出凭据。为避开本机已有的 PostgreSQL，Compose 将 Timescale 发布到 `DB_PORT`，默认 `15432`；容器间仍使用 `db:5432`。

Docker 完整启动：

```bash
INSTALL_ML=true docker compose up -d --build
```

不安装机器学习依赖时，可使用物理和几何策略；基线、PPO、训练和自动评估需要可选依赖。PPO 检查点必须匹配星座和观测空间。

| 环境配置 | 用途 |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | 浏览器 WebSocket 和前端 HTTP 代理的后端地址 |
| `SIMULATION_DATA_DIR` | 统一运行数据目录 |
| `SIMULATION_EPHEMERIS_FILE` | 星历路径，默认现有 `backend/de421.bsp` |
| `SIMULATION_TORCH_THREADS` | 推理 CPU 线程数，默认 1 |
| `INSTALL_ML` | Docker 是否安装机器学习依赖 |
| `DB_PORT` | 本机连接 Timescale 的端口，默认 15432 |

## 验证

仓库根目录：

```bash
.venv/bin/python scripts/generate_contracts.py --check
.venv/bin/python scripts/check_coding_rules.py
PYTHONPATH=backend MPLCONFIGDIR=/private/tmp/ophanim-mpl .venv/bin/python -m unittest discover -s backend/tests -v
```

前端目录：

```bash
npm run check:rules
npm run build
npm run test:browser
```

浏览器测试需要运行中的前后端及本机 Chrome。检查包含两个引擎的统一轨道与标识、独立会话、精确结束时间、项目迁移与删除、快照隔离、API、控制命令、记录窗口、基线与已有 PPO 模型推理。长时间 PPO 收敛训练不属于本次合并验证。
