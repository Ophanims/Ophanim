# 两个 Webapp 的统一合并

## 最终使用方式

Ophanim 与 SCOPE 已合为一个 Next.js Webapp 和一个 FastAPI 服务。所有项目进入同一个列表，使用同一份配置、同一个工作区、同一套运行控制与记录回放。旧项目与模型已完成导入，一次性迁移代码已移除。

| 功能 | 统一入口 |
| --- | --- |
| 应用标题、简介与开始入口 | `/` |
| 同页项目列表、创建、编辑、删除 | `/#projects`，原 `/dashboard` 自动跳转 |
| 项目工作区 | `/workspace/{project_id}` |
| 记录列表、下载、删除 | `/records` |
| 记录回放 | `/workspace/{project_id}?record_id={record_id}` |
| HTTP API | `/api/projects`、`/api/jobs/*`、`/api/records` |
| WebSocket | `/api/simulation/ws` |

工作区选择运行方式：Ophanim Physics、Geometry、L2D2、PHOENIX、MHSPO、PPO。它们是同一会话服务中的策略，使用共同的 `Project` 输入与 `SimulationSnapshot` 输出。两种 PHOENIX 实现的调度模型不同：Ophanim Physics 保留原物理任务模型中的调度策略，PHOENIX 选项运行迁入的基线环境。

Universe、Geometry、Object、Map、参数与数据流视图、分屏、配置、训练和评估都在统一工作区内。原来的仿真和记录 URL 重定向到此工作区。

首页与项目管理共用同一个地球场景。首次进入时先显示加载页，只有纹理加载并完成地球首帧渲染后才展示内容；点击 Get Started 原地展开项目管理，切换时不重建背景。背景加载失败时可重试，项目列表按需加载。

工作区最左侧活动栏分为 Satellites、Ground Stations、Network、Tasks 四个面板。地面站的新增、查看、编辑、删除及地图选点集中在 Ground Stations，保存后更新同一份项目 JSON；Parameters 不再编辑地面站、ROI 或 Mission。仿真连接期间地面站配置只读。

## 项目和记录

- 所有项目使用统一的 JSON 项目目录，数字 ID 保留为字符串。
- SCOPE 已迁入的项目与原有项目并列显示。修改、删除和运行都通过同一个 API。
- 配置与接口只接收规范名称和版本化契约。共同硬件配置使用 Hz；物理引擎使用的派生单位具有明确后缀。
- 原有处理器、电池、太阳能板与静态功率参数纳入共同的 `resources` 配置，地面站保留 `altitude_m`。
- 新记录在 TimescaleDB 的独立 `ophanim` schema 中保存与实时展示同源的完整快照及按领域分类的分析点，附带完整项目配置、算法、代码哈希和版本。历史回放无需依赖仍然存在的项目。
- 文件记录和失败恢复日志可通过 `scripts/import_record_files.py` 幂等导入当前 TimescaleDB；导入保留源文件。

本机已迁入 SCOPE 的项目、模型与归一化文件，运行时直接读取统一目录。

默认运行数据位于 `data/ophanim/`：

```text
projects/          # 唯一项目目录，类型化 JSON
records/           # 保留的旧文件记录，可显式导入数据库
record_recovery/   # 未完成数据库提交的恢复日志，成功提交后移除
models/            # 导入检查点、按项目保存的训练版本
output/            # 评估结果、日志、图表
```

项目文件不提交到 Git；迁移到其他机器时应备份此目录，并单独备份 TimescaleDB（本机默认位于 `data/timescale/`）。HTTP 接口不接收 pickle。

## 代码组织和编码规则

```text
backend/simulator/
  schemas/         # 唯一项目配置契约
  contracts.py     # 状态、命令和 WebSocket 消息
  core/            # 统一会话与各运行策略
  entities/        # 实体及 Snapshot
  models/          # 轨道、相机与地理计算
  env/             # 基线、PPO、训练与评估
  services/        # 项目目录、模型、实时运行、记录、恢复、后台任务
  routers/         # 唯一 HTTP / WebSocket 边界
backend/core/      # 原物理内核，时钟、世界和预测缓存按会话隔离
backend/entity/    # 原物理任务模型与实体
backend/persistence/ # TimescaleDB 记录与分析仓库
frontend/src/features/simulation/
  contracts/       # 从后端生成的 TypeScript、JSON Schema、默认配置和路由
  communication/   # 所有请求、边界验证和 WebSocket 生命周期
  app/             # 项目、配置、工作区与可视化
  components/      # 展示组件与资源回收
frontend/src/app/   # 单一应用的页面和同源 API 代理
```

字段含义与单位见 [共享概念名称表](CONTRACT_NAMES.md)。遵循 [CODING_RULES.md](../CODING_RULES.md)：手写文件不超过 500 行；领域对象与快照分离；JSON 由契约模型导出；共享字段采用 `snake_case`；通信集中管理；显示与记录同源；会话独立管理时间、随机数、身份及缓存。原有两套页面、Controller 和仿真通信入口已移除。

原物理内核仍保留部分历史实现细节，例如实体内部的旧资源常量命名和算法对同一聚合内实体的引用；共享配置、公开接口、页面和记录契约已统一。规范检查不等同于对所有领域语义的形式化证明。

完整记录在 TimescaleDB 中按批次提交；前端仅缓冲最近 600 个接收帧，分页回放每次最多 600 帧。显示可以跳帧，完整记录不跳步。启动时只构造模型，轨道、地面站和 ROI 坐标按步计算；PHOENIX 需要的未来日照按请求窗口计算，算法决策代码不变。训练使用单独进程，支持查询和取消；应用关闭时回收。新训练版本保存完整后才切换项目模型指针，导入的检查点不会被覆盖。

## 本地启动

项目仍使用本地文件目录；回放和分析记录使用 TimescaleDB。已有 `DATABASE_URL` 时直接连接，否则使用 `.env` 的 `DB_USER`、`DB_PASSWORD`、`DB_NAME` 启动专用本机数据库。

```bash
./setup.sh --ml
./start.sh
# 关闭：Ctrl+C 或另一个终端执行 ./stop.sh
```

脚本读取 `.env` 中的端口配置，统一前后端地址，按需要构建前端，并负责子进程退出与端口检查。具体命令、数据库备份和文件记录导入方式见 [README](../README.md)。唯一数据库为 TimescaleDB，使用 `ophanim` schema 和本机 `data/timescale/` 目录。停止应用不会停止或删除数据库。

## 验证

仓库根目录：

```bash
.venv/bin/python scripts/generate_contracts.py --check
.venv/bin/python scripts/check_coding_rules.py
PYTHONPATH=backend MPLCONFIGDIR=/private/tmp/ophanim-mpl .venv/bin/python -m unittest discover -s backend/tests -v
.venv/bin/python scripts/test_record_database.py
```

前端目录：

```bash
npm run check:rules
npm run build
npm run test:browser
```

浏览器测试需要运行中的前后端及本机 Chrome。检查包含两个引擎的统一轨道与标识、独立会话、精确结束时间、JSON 项目保存与删除、快照隔离、API、控制命令、记录窗口、基线与已有 PPO 模型推理。长时间 PPO 收敛训练不属于本次合并验证。
