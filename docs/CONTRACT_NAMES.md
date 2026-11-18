# 共享概念名称表

权威字段、类型、默认值与约束来自 `backend/simulator/schemas/`、`contracts.py` 和服务中的类型化响应模型。前端 `contracts/` 由 `scripts/generate_contracts.py` 生成，禁止手工修改。此表解释概念、单位与兼容范围，不是第二套传输模型。

| 规范名称 | 含义、单位与作用域 | 历史名称与迁移边界 |
| --- | --- | --- |
| `schema_version` | 项目、快照、记录的契约版本 | 无版本的旧数据属于 v0，仅迁移工具接收 |
| `project_id` | 项目唯一标识，字符串；原数字 ID 保留其十进制文本 | `projectId`、项目顶层 `id` 仅在 v0 适配器读取 |
| `record_id` | 记录唯一标识；新记录为 UUID，历史记录为 `timescale_{旧ID}` | `recordId` 仅属于旧协议 |
| `id` | 所在类型的实体／配置标识；记录查询中通过 `record_id` 和类型确定作用域 | 实体通信地址不等同于此标识 |
| `addr` | 原物理内核单次会话中的通信地址 | 仅聚合内部使用；对外关联解析为实体 `id` |
| `title` | 项目标题 | 原项目 `name` 只在 v0 项目迁移时转换；实体 `name` 是不同概念 |
| `algorithm` | 当前项目选择的运行策略，值由共享契约限定 | 不再通过另一套页面选择引擎 |
| `seed` | 可复现运行的随机种子 | 前后端、项目、记录同名 |
| `resources` | 处理器、电源与物理调度资源配置 | 原 camelCase 项目字段仅在 v0 入口读取 |
| `hardware` | 成像与无线链路硬件配置 | 旧嵌套硬件字段由离线迁移工具读取 |
| `ground_stations` | 地面站配置集合 | `groundStations` 仅在旧 SCOPE 数据迁移时读取 |
| `altitude_m` | 地面站海拔，米 | 旧数据库站点 `altitude` 仅在适配器读取 |
| `constellation.altitude` | 星座轨道高度，米 | 与地面站海拔属于不同配置作用域 |
| `location` / `loc` | 配置中的地理位置／快照中的瞬时星下点；子字段为 `lat`、`lon`，角度 | 配置位置与运行时瞬时位置是不同状态概念 |
| `pos` | 瞬时地心惯性坐标，米；轴顺序 `x`、`y`、`z` | 渲染缩放及轴变换只在视图边界执行 |
| `time` | 当前仿真快照时刻，ISO 8601，包含时区；时序表中为同一时刻的 `TIMESTAMPTZ`，不使用实际写入时间代替 | 旧时钟字段由历史快照适配器转换 |
| `start_time` / `end_time` | 配置中的起止时刻，ISO 8601 | `startTime`、`endTime` 仅在迁移入口读取 |
| `time_slot` | 外层几何／物理时间步长，秒 | 不表示帧序号，也不表示算法内部动作序号 |
| `frame_counter` | 会话快照的帧序号，从 0 开始 | 页面时钟组件也使用此名称 |
| `period_counter` | 外层轨道采样位置序号 | 与帧序号可能因算法内部动作而不同 |
| `slot_counter` | 一个外层采样周期内的调度子步序号 | 不能与秒单位的 `time_slot` 混用 |
| `battery_percent` | 电量百分数，0–100 | 原 `batteryLevel` 在历史记录入口转换 |
| `processor_clock_frequency_ghz` | 瞬时处理器频率，GHz | 原 `processorClockFrequency` 只在 v0 记录入口读取 |
| `max_clock_frequency_ghz` | 配置允许的最高处理器频率，GHz | 与瞬时频率属于不同概念 |
| `src` / `dst` | 链路端点实体标识 | 原物理地址在形成统一快照时解析为实体标识 |
| `distance` | 链路距离，米 | 保留共同契约的规范名称 |
| `rate` | 链路传输速率，bit/s | 旧链路 `capacity` 只在物理聚合边界与 v0 记录适配器转换 |
| `snr` | 链路信噪比，dB | 两种内核形成统一快照时保持同一尺度 |
| `is_observing` / `is_processing` | 当前观测／计算状态 | 旧 `onROI`、`onCOM` 仅由历史入口接收 |
| `is_communicating_sgl` / `is_communicating_isl` | 当前星地／星间通信状态 | 旧 `onSGL`、`onISL` 仅由历史入口接收 |
| `is_charging` | 当前受光／充电状态 | 旧 `onSUN` 仅由历史入口接收 |
| `tasks` | 基线和 PPO 环境中的推理任务快照 | 与物理内核的任务生命周期不同 |
| `missions` | 物理内核任务快照 | 不把不同任务模型的字段强行视为同义 |
| `entity_type` | 分析数据类型：`satellites`、`stations`、`tasks`、`missions`、`links`、`network` | 与快照集合名一致 |
| `created_at` | 记录元数据的实际创建时间，与仿真 `time` 分开 | 不作为回放时间 |
| `average_battery_percent` | 当前快照中全部卫星的平均电量百分数；无卫星时为 0 | 从同一快照派生 |
| `start_point` / `next_start_point` | 固定帧窗口内的分析点分页偏移／下一页偏移；下一页为空表示结束 | 与实体数可能大于帧数的分析查询配套 |

频率、带宽在共同硬件配置中统一使用 `*_frequency_hz`、`*_bandwidth_hz`。物理公式确实需要 GHz／MHz 时，派生字段明确使用 `*_frequency_ghz`、`*_bandwidth_mhz`，转换集中在 `EngineConfig.from_project()`。

环境配置键在环境读取和配置模块中保留大写名称：`SIMULATION_DATA_DIR`、`SIMULATION_EPHEMERIS_FILE`、`SIMULATION_TORCH_THREADS`、`SIMULATION_PUSH_INTERVAL_S`、`DATABASE_URL`、`NEXT_PUBLIC_API_URL`。`SIMULATION_PUSH_INTERVAL_S` 只控制实时展示通知频率，不改变算法步长和完整记录频率。各派生文件目录由唯一的 `SIMULATION_DATA_DIR` 生成。

v0 兼容入口仅包括旧 MySQL／Timescale 迁移和离线 SCOPE 项目导入；迁移完成的对象写入版本化规范契约，运行 API 不接收旧别名。所有需要保留的 v0 数据转换并完成部署升级后，可删除这些适配器和旧库初始化模块。
