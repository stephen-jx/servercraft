# ServerCraft 🛠️

一个远程服务器环境初始化平台，支持可视化管理服务器、选择组件、并行安装、实时日志。

## 功能特性

- 🖥️ **服务器管理** - 添加服务器、检测系统信息、批量操作
- 📦 **组件安装** - 38+ 组件，支持并行安装、依赖处理
- ⚙️ **系统配置** - 软件源、时区、DNS、内核参数
- 📊 **实时日志** - WebSocket 推送安装进度
- 🔐 **认证系统** - JWT Token 认证

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Ant Design 5 + TypeScript + Vite |
| 后端 | FastAPI + SQLAlchemy 2.0 + asyncssh |
| 数据库 | SQLite / PostgreSQL |
| 认证 | JWT (python-jose) + bcrypt |

## 快速开始

### 方式一：直接运行

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

### 方式二：Docker Compose

```bash
docker-compose up -d
```

## 访问地址

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 默认账号

第一个注册的用户自动成为管理员。

## 组件列表

### 系统基础 (21个)
- 软件源配置: apt/yum, pip, npm, Docker, Maven
- 系统设置: 时区, 主机名, DNS, NTP, 字符集
- 性能调优: 内核参数, ulimit, Swap

### 数据库 (4个)
MySQL, PostgreSQL, Redis, MongoDB

### 中间件 (2个)
Nginx, Apache

### 容器 (2个)
Docker, Kubernetes

### 消息队列 (2个)
RabbitMQ, Kafka

### 监控 (2个)
Prometheus, Grafana

### 开发环境 (5个)
Node.js, Python, Go, Java, Git

## 项目结构

```
servercraft/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 路由
│   │   ├── core/            # 核心模块 (config, auth, database)
│   │   ├── models/          # 数据模型
│   │   └── services/        # 业务逻辑
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── layouts/         # 布局组件
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | 数据库连接 | sqlite+aiosqlite:///./servercraft.db |
| SECRET_KEY | JWT 密钥 | 自动生成 |
| ALLOWED_ORIGINS | CORS 允许来源 | http://localhost:3000 |

## License

MIT