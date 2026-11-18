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

工作区选择调度策略：Ophanim、Geometry、L2D2、PHOENIX、MHSPO、PPO。它们全部使用唯一的 `Simulation` 环境、共同的 `Project` 输入与 `SimulationSnapshot` 输出。Ophanim 保留原有调度公式，PHOENIX 保留迁入的基线调度公式；Geometry 提交空动作，环境仍按统一规则推进。

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
  core/            # 唯一 Simulation、状态转移与提交循环
  entities/        # 实体及 Snapshot
  models/          # 轨道、相机与地理计算
  policies/        # 纯决策、策略记忆与只读输入视图
  env/             # Gym 输入输出适配、训练与评估；不实现物理环境
  services/        # 项目目录、模型、实时运行、记录、恢复、后台任务
  routers/         # 唯一 HTTP / WebSocket 边界
backend/core/      # 历史类型依赖与预测缓存；旧世界循环已删除
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

旧实体类型仅保留历史记录契约等兼容依赖。运行时不再创建独立的物理世界、基线 env 或 PPO env。规范检查不等同于对所有领域语义的形式化证明。

## 统一状态转移

运行模型共同继承 `core/model.py` 的 `SimulationModel`，提供 `snapshot()` 和 `transition(action, context)`。卫星、基站、链路、任务、网络及几何实体保留各自的状态字段与物理方程；`StepContext` 显式携带当前仿真时间、`dt_s` 和帧号。项目配置模型与运行模型分开。

每次 `SimulationSession.step()` 经过同一个 `SimulationKernel`：

```text
已提交状态 s_t
  → 复制可变运行状态、队列、随机数与策略记忆
  → 根据 s_t 收集整个时隙的动作 a_t
  → 按模型执行 transition(a_t, Δt)
  → 统一推进时钟、实时计算该时刻的轨道和链路
  → 验证完整 SimulationSnapshot
  → 一次性替换运行状态，得到 s_t+1
  → 同一份快照写入 TimescaleDB，并供 WebSocket 展示
```

`Simulation(project)` 是唯一环境，负责实体创建、种子与任务生成、链路、能耗、任务进度、时钟及终止条件。所有策略都使用项目的 `experiment.time_slot`（秒，默认 30），取消各算法内原有的 10 秒、0.5 秒等独立步长；细粒度仿真和 PPO 训练可把同一项目参数设为 0.5。相同配置与种子的初始世界完全相同，相同动作的转移结果与算法名称无关。

策略位于 `policies/`，只保留决策方法与策略记忆。基线的队列/预测和 Ophanim 的原调度方程保留；策略通过脱离模拟器的 `PlanningView` 读取任务、节点、链路与按需预测。原来的 `L2D2Env`、`PhoenixEnv`、`MHSPOEnv`、`PPOEnv`、`PhysicsEnvironment`、`LEOEnv` 及旧世界循环已删除。Ophanim 的旧式输入转换为观察对象，并将输出翻译为共同动作；观察对象不拥有任务生命周期，也不执行物理更新。原先未被触发的截止时间访问缺失方法已补全。

算法决策阶段不更新模拟器的电量、任务进度或时钟。带宽分配、计算完成度、每颗卫星每时隙的一次能量结算，全部由 `core/world_transition.py` 和模型的 `transition()` 实现。相对带宽权重属于 `TransferAction.weight`，基线默认等权，PPO 继续按层输出量给出权重。不同算法不再选择不同的物理公式或完成度计算分支。活跃任务年龄每时隙增加一次；最后不足一整个时隙时使用实际 `dt_s`。

`SimulationSession` 只选择策略，不选择环境。执行前暂存模拟器和策略记忆，完整快照验证成功后一次提交；执行失败时旧时钟、RNG、任务和策略记忆不变。`Simulation.step(actions)` 也提供同样的原子提交语义，供训练适配器直接使用。几何输入与有限纯计算缓存共享，不复制 SGP4 或文件句柄。

PPO 的 `SimulationGymAdapter` 只是 `Simulation` 的 Gym 输入输出适配器。它逐任务收集动作，然后调用同一个模拟器；没有自己的实体、计时、任务生成或物理规则。动作空间、特征公式、奖励函数、掩码规则和已有权重保留。PPO 推理也在同一帧状态下收集所有动作，并由共同环境统一执行。统一任务和时间步长会改变旧轨迹；长时间策略收敛需要另行评估。

自定义 Python 策略实现 `DecisionPolicy.decide(state, context) -> SchedulingActions`，通过 `SimulationSession(project, algorithm, policy=...)` 注入任意算法标签下的同一个环境。它接收脱离运行对象的快照，返回 `ComputeAction(task_id, node_id)`、`TransferAction(task_id, src, dst, kind, weight)`；持续动作也需包含在本时隙动作集合中。API 的策略列表保持现有六项。

`Task` 是唯一运行任务对象，`TaskSnapshot` 是只读传输契约。新记录的全部算法都使用 `tasks`；`missions` 字段和历史任务类型仅保留旧记录读取兼容。`workload_done` 允许小数以表达部分时隙的计算进度。记录用于展示回放与分析，不包含 RNG、策略记忆等完整恢复信息。

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

浏览器测试需要运行中的前后端及本机 Chrome。检查包含各策略共享同一环境、种子、任务与状态转移，训练适配器和直接调用的一致性、统一轨道与标识、独立会话、精确结束时间、JSON 项目保存与删除、快照隔离、API、控制命令、记录窗口、基线与已有 PPO 模型推理。长时间 PPO 收敛训练不属于本次合并验证。
