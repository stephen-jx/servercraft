# 数据库设计文档

## 数据库选型

| 环境 | 数据库 | 连接字符串 |
|------|--------|-----------|
| 开发 | SQLite | `sqlite+aiosqlite:///./servercraft.db` |
| 生产 | PostgreSQL 15 | `postgresql+asyncpg://user:pass@host:5432/servercraft` |

---

## ER 图

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id (PK)         │
│ username        │
│ password_hash   │
│ email           │
│ is_active       │
│ is_admin        │
│ last_login      │
│ created_at      │
└─────────────────┘

┌─────────────────┐       ┌─────────────────────┐
│     Server      │       │  ServerComponent    │
├─────────────────┤       ├─────────────────────┤
│ id (PK)         │◄──────│ id (PK)             │
│ name            │  1:N  │ server_id (FK)      │
│ ip_address      │       │ component_name      │
│ port            │       │ component_version   │
│ username        │       │ status              │
│ password        │       │ install_path        │
│ ssh_key         │       │ installed_at        │
│ os_type         │       └─────────────────────┘
│ os_version      │
│ arch            │       ┌─────────────────────┐
│ cpu_cores       │       │       Task          │
│ memory_mb       │       ├─────────────────────┤
│ disk_gb         │◄──────│ id (PK)             │
│ status          │  1:N  │ server_id (FK)      │
│ created_at      │       │ task_type           │
└─────────────────┘       │ component_names     │
                          │ status              │
                          │ progress            │
                          │ output              │
                          │ started_at          │
                          │ completed_at        │
                          │ created_at          │
                          └─────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
                          ┌─────────────────────┐
                          │      SubTask        │
                          ├─────────────────────┤
                          │ id (PK)             │
                          │ task_id (FK)        │
                          │ component_name      │
                          │ status              │
                          │ started_at          │
                          │ completed_at        │
                          │ error_message       │
                          └─────────────────────┘
```

---

## 表结构详情

### 1. users (用户表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| username | VARCHAR(50) | 用户名，唯一 |
| password_hash | VARCHAR(255) | bcrypt 加密的密码 |
| email | VARCHAR(100) | 邮箱 |
| is_active | BOOLEAN | 是否激活 |
| is_admin | BOOLEAN | 是否管理员 |
| last_login | DATETIME | 最后登录时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**索引**:
- `idx_users_username` ON (username)

---

### 2. servers (服务器表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| name | VARCHAR(255) | 服务器名称 |
| ip_address | VARCHAR(45) | IP 地址，唯一 |
| port | INTEGER | SSH 端口，默认 22 |
| username | VARCHAR(255) | SSH 用户名 |
| password | VARCHAR(255) | SSH 密码 (加密存储) |
| ssh_key | TEXT | SSH 私钥 |
| os_type | VARCHAR(50) | 系统类型 (ubuntu/centos) |
| os_version | VARCHAR(50) | 系统版本 |
| arch | VARCHAR(20) | 架构 (x86_64/arm64) |
| cpu_cores | INTEGER | CPU 核心数 |
| memory_mb | INTEGER | 内存 (MB) |
| disk_gb | INTEGER | 磁盘 (GB) |
| status | ENUM | 状态 (pending/connected/failed/busy) |
| last_check_at | DATETIME | 最后检测时间 |
| error_message | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**索引**:
- `idx_servers_ip` ON (ip_address)
- `idx_servers_status` ON (status)

---

### 3. tasks (任务表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| server_id | INTEGER | 关联服务器 ID |
| task_type | ENUM | 类型 (install/uninstall) |
| component_names | JSON | 组件名称列表 |
| status | ENUM | 状态 (pending/running/success/failed/cancelled) |
| progress | INTEGER | 进度 (0-100) |
| current_step | VARCHAR(255) | 当前步骤 |
| output | TEXT | 执行日志 |
| options | JSON | 组件选项 |
| started_at | DATETIME | 开始时间 |
| completed_at | DATETIME | 完成时间 |
| duration_seconds | INTEGER | 耗时 (秒) |
| error_message | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |

**索引**:
- `idx_tasks_server` ON (server_id)
- `idx_tasks_status` ON (status)
- `idx_tasks_created` ON (created_at)

---

### 4. subtasks (子任务表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| task_id | INTEGER | 关联任务 ID |
| component_name | VARCHAR(100) | 组件名称 |
| status | ENUM | 状态 |
| started_at | DATETIME | 开始时间 |
| completed_at | DATETIME | 完成时间 |
| error_message | TEXT | 错误信息 |

**索引**:
- `idx_subtasks_task` ON (task_id)

---

### 5. server_components (已安装组件表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| server_id | INTEGER | 关联服务器 ID |
| component_name | VARCHAR(100) | 组件名称 |
| component_version | VARCHAR(50) | 版本 |
| status | VARCHAR(20) | 状态 (installed/running/stopped) |
| install_path | VARCHAR(500) | 安装路径 |
| config_path | VARCHAR(500) | 配置路径 |
| installed_at | DATETIME | 安装时间 |

**索引**:
- `idx_server_components_server` ON (server_id)
- `idx_server_components_name` ON (component_name)

---

## 关系说明

| 关系 | 类型 | 说明 |
|------|------|------|
| User → Task | 1:N | 一个用户可创建多个任务 (未来扩展) |
| Server → Task | 1:N | 一个服务器可有多个任务 |
| Task → SubTask | 1:N | 一个任务包含多个子任务 |
| Server → ServerComponent | 1:N | 一个服务器可安装多个组件 |

---

## 数据流

```
用户操作
    │
    ▼
创建 Task (status=pending)
    │
    ▼
TaskRunner 执行
    │
    ├── 创建 SubTask (每个组件)
    │
    ├── SSH 连接 Server
    │
    ├── 执行安装命令
    │
    ├── 更新 SubTask status
    │
    ├── 更新 Task progress
    │
    └── 完成后创建 ServerComponent
```

---

## 迁移命令

```bash
# 自动创建表
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 或使用 SQLAlchemy 自动创建
# 应用启动时自动创建 (init_db)
```