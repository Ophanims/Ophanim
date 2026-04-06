# Ophanim

## 数据库可视化入口

- TimescaleDB（PostgreSQL）可视化：pgAdmin
	- 地址：`http://localhost:5050`
	- 登录账号：`${PGADMIN_DEFAULT_EMAIL}`
	- 登录密码：`${PGADMIN_DEFAULT_PASSWORD}`

- MySQL 可视化：Adminer
	- 地址：`http://localhost:8081`

## 预置书签说明（建议）

可在浏览器或团队文档中保存以下“登录参数书签”，方便快速连接。

### 1) pgAdmin 登录书签（Web 登录）

- URL：`http://localhost:5050`
- Email：`${PGADMIN_DEFAULT_EMAIL}`
- Password：`${PGADMIN_DEFAULT_PASSWORD}`

### 2) pgAdmin 服务器连接书签（连接 TimescaleDB）

在 pgAdmin 内 Register Server 时填写：

- Name：`ophanim-timescaledb`
- Host name/address：`db`
- Port：`5432`
- Maintenance database：`${DB_NAME}`
- Username：`${DB_USER}`
- Password：`${DB_PASSWORD}`

### 3) Adminer 连接书签（连接 MySQL）

在 Adminer 登录页填写：

- System：`MySQL`
- Server：`mysql`
- Username：`${MYSQL_USER}`
- Password：`${MYSQL_PASSWORD}`
- Database：`${MYSQL_DATABASE}`

## 启动命令

启动数据库与可视化服务：

`docker compose up -d db mysql pgadmin adminer`