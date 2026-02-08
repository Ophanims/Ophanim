# 软件需求规格说明书 (SRS)

**Software Requirements Specification**

**项目名称**: Ophanim Simulator
**版本号**: 0.1.0
**日期**: 2026-02-08
**作者**: OSSP

---

## 修订历史 (Revision History)

| 版本 | 日期 | 修改描述 | 作者 | 审批人 |
| --- | --- | --- | --- | --- |
| 0.1.0 | 2023-10-XX | 初始草稿创建，定义核心架构与物理层需求 | OSSP | - |
|  |  |  |  |  |

---

## 1. 简介 (Introduction)

### 1.1 目的 (Purpose)

本文档旨在定义 **[项目名称]** 的详细软件需求。该系统是一个面向科研的高保真卫星星座仿真平台，旨在支持 **轨道边缘计算 (Orbital Edge Computing)**、**星间链路网络 (ISL)** 及 **智能协同算法 (如 RL, Bend-pipe)** 的验证与可视化。
本文档的预期读者包括系统架构师、前端/后端开发人员、算法研究人员及测试工程师。

### 1.2 范围 (Scope)

本软件系统将包含以下核心模块：

1. **物理仿真内核**：基于 SGP4/SDP4 的轨道传播与几何计算。
2. **资源与网络模型**：模拟卫星电量、计算资源及动态网络拓扑。
3. **算法沙箱接口**：支持科研人员通过标准 API 接入自定义调度算法。
4. **可视化前端**：基于 Web 的 3D 交互式监控大屏。

### 1.3 定义与缩略语 (Definitions & Acronyms)

* **TLE**: Two-Line Element Set，两行轨道根数。
* **ISL**: Inter-Satellite Link，星间链路。
* **GSL**: Ground-Satellite Link，星地链路。
* **OEC**: Orbital Edge Computing，轨道边缘计算。
* **Agent**: 在强化学习环境中代表单颗卫星或整个星座的智能体。

---

## 2. 总体描述 (Overall Description)

### 2.1 产品视角 (Product Perspective)

本系统是一个独立的仿真平台，后端采用 **FastAPI + Python (Skyfield)** 进行物理计算，前端采用 **Next.js + Three.js** 进行展示，数据存储于 **PostgreSQL (TimescaleDB)**。系统需支持离散事件仿真 (Discrete Event Simulation)。

### 2.2 用户特征 (User Characteristics)

* **算法研究员 (Researcher)**：关注数据的导出、算法接口的易用性、仿真结果的可复现性。
* **系统管理员 (Admin)**：关注系统部署、配置管理及多用户并发性能。

### 2.3 假设与依赖 (Assumptions and Dependencies)

* 假设服务器具备足够的算力支持 100+ 卫星的实时轨道计算。
* 依赖 NASA/Celestrak 提供的公开 TLE 数据源。
* 依赖 Python 3.9+ 及 Node.js 18+ 环境。

---

## 3. 系统特性/功能需求 (System Features)

*注意：需求编号格式建议为 FR-[模块]-[编号]*

### 3.1 物理与轨道环境 (Physical Layer)

**FR-PHY-01: 轨道传播 (Orbit Propagation)**

* **描述**: 系统必须能够读取 TLE 数据，并基于 SGP4 算法计算任意给定时间点的卫星位置与速度。
* **输入**: TLE 文件, 仿真时间戳 。
* **输出**: 卫星在 J2000 (ECI) 和 ECEF 坐标系下的位置向量  和速度向量 。
* **验收标准**: 与 GMAT 或 STK 软件对比，24小时内位置误差 < 1km。

**FR-PHY-02: 覆盖性分析 (Coverage Analysis)**

* **描述**: 系统需根据卫星载荷的视场角 (FOV) 和姿态，计算其对地面的覆盖区域。
* **逻辑**: 当地面目标点位于卫星视锥体 (Sensor Cone) 内且满足最小仰角限制时，判定为“可见”。

**FR-PHY-03: 能源环境 (Energy Environment)**

* **描述**: 系统需根据太阳位置计算卫星是否处于阴影区 (Eclipse)，并据此切换充电/放电状态。

**FR-PHY-04: 星座自动生成器 (Constellation Generator)**
* **描述**: 系统应支持用户通过输入 Walker 星座参数 (Total Satellites $N$, Planes $P$, Phasing $F$) 自动生成大规模虚拟星座。
* **逻辑**: 系统根据 Walker-Delta 或 Walker-Star 公式计算每颗卫星的初始相位，并生成对应的虚拟 TLE。

### 3.2 网络与通信 (Network Layer)

**FR-NET-01: 动态拓扑生成 (Dynamic Topology)**

* **描述**: 在每个仿真步长，系统需计算所有卫星对之间的距离。若距离 < 最大通信距离且无地球遮挡 (Line-of-Sight)，则建立潜在 ISL 连接。
* **约束**: 每颗卫星最多同时建立 4 条 ISL 链路（可配置）。

**FR-NET-02: 数据传输模拟 (Data Transmission)**

* **描述**: 模拟数据包在链路上的传输，计算传输延迟 (Propagation Delay) 和传输时间 (Transmission Delay)。

### 3.3 边缘计算与资源 (Computing Layer)

**FR-COMP-01: 任务队列管理 (Task Queue)**

* **描述**: 每颗卫星需维护一个任务队列（如：待处理的图像数据）。
* **行为**: 任务不仅占用存储空间，处理任务时还需占用 CPU 时间并消耗额外电量。

**FR-COMP-02: 电池模型 (Battery Model)**

* **公式**: 。
* **约束**: 电量耗尽时，卫星进入“失效”或“休眠”状态，无法执行任务。

### 3.4 算法接口与控制 (Algorithm Interface)

**FR-ALG-01: 状态观测 (Observation API)**

* **描述**: 系统提供 API 返回当前的全局或局部状态 。
* **数据结构**: JSON 格式，包含位置、电量、邻居列表、任务队列长度。

**FR-ALG-02: 动作执行 (Action Execution)**

* **描述**: 系统接收算法输出的动作向量  并应用到仿真环境。
* **动作空间**:
* `IDLE`: 待机
* `OBSERVE`: 对地观测（消耗电量，增加存储）
* `COMPUTE`: 边缘处理（消耗大量电量，减少存储，获得奖励）
* `TRANSMIT`: 数据下传/转发



---

## 4. 外部接口需求 (External Interface Requirements)

### 4.1 用户界面 (User Interfaces)

* **UI-01**: 3D 地球视图，支持缩放、旋转，显示卫星轨道轨迹。
* **UI-02**: 实时仪表盘，显示全网平均延迟、任务积压量、存活卫星数量。
* **UI-03**: 配置面板，允许用户上传 YAML/JSON 配置文件以设定仿真参数。

### 4.2 软件接口 (Software Interfaces)

* **数据库接口**: 使用 SQLAlchemy (ORM) 读写 PostgreSQL。
* **算法 SDK**: 提供 Python Client (`pip install satedge-sim`)，封装 HTTP/WebSocket 通信细节。

### 4.3 通信接口 (Communication Interfaces)

* **REST API**: 用于仿真初始化、暂停、重置、获取历史数据。
* **WebSocket**: 用于前端实时接收 3D 渲染所需的坐标流 (Stream)。

---

## 5. 非功能性需求 (Non-Functional Requirements)

### 5.1 性能需求 (Performance)

* **NFR-PERF-01**: 支持至少 500 颗卫星的星座规模。
* **NFR-PERF-02**: 仿真步进速度 (Simulation Ratio) 可调，最大支持 100x 实时速度（即 1秒钟计算出 100秒的物理状态）。

### 5.2 可靠性与准确性 (Reliability & Accuracy)

* **NFR-REL-01**: 确定性 (Determinism)。在相同的随机种子 (Seed) 下，多次运行仿真必须产生完全一致的结果。

### 5.3 扩展性 (Extensibility)

* **NFR-EXT-01**: 添加新的路由协议或任务类型时，无需重构核心物理引擎。

---

## 6. 数据需求 (Data Requirements)

### 6.1 数据库 Schema 概要

* **Project Config Table**: 存储仿真配置 (JSONB)。
* **Simulation States Table**: 时序超表 (Hypertable)，存储 `(time, sat_id, state_vector)`。
* **Experiments Metrics Table**: 存储每次实验的汇总指标 (KPIs)。

---

## 7. 附录 (Appendices)

* **附录 A**: 坐标系转换公式参考 (J2000 to ECEF)。
* **附录 B**: 默认使用的 TLE 示例文件。

---