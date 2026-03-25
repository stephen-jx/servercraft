"""Component registry - defines all available components."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class ComponentCategory(str, Enum):
    SYSTEM = "system"           # 系统基础配置
    DATABASE = "database"
    MIDDLEWARE = "middleware"
    MESSAGE_QUEUE = "message_queue"
    CONTAINER = "container"
    MONITORING = "monitoring"
    DEVELOPMENT = "development"
    OTHER = "other"


@dataclass
class ComponentOption:
    """Component installation option."""
    name: str
    label: str
    type: str  # string, number, boolean, select
    default: Optional[str] = None
    required: bool = False
    options: Optional[List[str]] = None  # for select type
    description: Optional[str] = None


@dataclass
class Component:
    """Component definition."""
    name: str
    display_name: str
    category: ComponentCategory
    description: str
    playbook: str  # Ansible playbook name
    supported_os: List[str] = field(default_factory=lambda: ["ubuntu", "centos", "debian"])
    default_version: Optional[str] = None
    versions: List[str] = field(default_factory=list)
    options: List[ComponentOption] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # other components required
    ports: List[int] = field(default_factory=list)
    icon: Optional[str] = None


# Component Registry
COMPONENT_REGISTRY: Dict[str, Component] = {
    # ========================================
    # === SYSTEM - 系统基础配置 ===
    # ========================================
    
    # --- 软件源配置 ---
    "apt-mirror": Component(
        name="apt-mirror",
        display_name="系统软件源",
        category=ComponentCategory.SYSTEM,
        description="配置 Ubuntu/Debian apt 软件源镜像",
        playbook="apt-mirror",
        options=[
            ComponentOption("mirror", "镜像源", "select", default="aliyun", 
                options=["aliyun", "tsinghua", "ustc", "huawei", "tencent"]),
            ComponentOption("update", "立即更新", "boolean", default="true"),
        ],
        icon="mirror",
    ),
    "yum-mirror": Component(
        name="yum-mirror",
        display_name="系统软件源 (RHEL系)",
        category=ComponentCategory.SYSTEM,
        description="配置 CentOS/RHEL yum 软件源镜像",
        playbook="yum-mirror",
        supported_os=["centos", "rocky", "almalinux", "rhel"],
        options=[
            ComponentOption("mirror", "镜像源", "select", default="aliyun",
                options=["aliyun", "tsinghua", "ustc", "huawei", "tencent"]),
            ComponentOption("update", "立即更新", "boolean", default="true"),
        ],
        icon="mirror",
    ),
    "pip-mirror": Component(
        name="pip-mirror",
        display_name="pip 镜像源",
        category=ComponentCategory.SYSTEM,
        description="配置 Python pip 镜像源",
        playbook="pip-mirror",
        options=[
            ComponentOption("mirror", "镜像源", "select", default="aliyun",
                options=["aliyun", "tsinghua", "tencent", "douban"]),
            ComponentOption("trusted_host", "信任主机", "boolean", default="true"),
        ],
        icon="python",
    ),
    "npm-mirror": Component(
        name="npm-mirror",
        display_name="npm 镜像源",
        category=ComponentCategory.SYSTEM,
        description="配置 Node.js npm 镜像源",
        playbook="npm-mirror",
        options=[
            ComponentOption("mirror", "镜像源", "select", default="taobao",
                options=["taobao", "tencent", "huawei"]),
        ],
        icon="nodejs",
    ),
    "docker-registry": Component(
        name="docker-registry",
        display_name="Docker 镜像加速",
        category=ComponentCategory.SYSTEM,
        description="配置 Docker Hub 镜像加速器",
        playbook="docker-registry",
        dependencies=["docker"],
        options=[
            ComponentOption("registry", "镜像加速地址", "select", default="aliyun",
                options=["aliyun", "tencent", "ustc", "custom"]),
            ComponentOption("custom_url", "自定义加速地址", "string", 
                description="选择 custom 时输入完整加速地址"),
        ],
        icon="docker",
    ),
    "maven-mirror": Component(
        name="maven-mirror",
        display_name="Maven 仓库",
        category=ComponentCategory.SYSTEM,
        description="配置 Maven 中央仓库镜像",
        playbook="maven-mirror",
        options=[
            ComponentOption("mirror", "镜像源", "select", default="aliyun",
                options=["aliyun", "huawei", "tencent"]),
        ],
        icon="java",
    ),
    
    # --- 系统设置 ---
    "timezone": Component(
        name="timezone",
        display_name="时区设置",
        category=ComponentCategory.SYSTEM,
        description="设置系统时区",
        playbook="timezone",
        options=[
            ComponentOption("timezone", "时区", "select", default="Asia/Shanghai",
                options=["Asia/Shanghai", "Asia/Hong_Kong", "Asia/Tokyo", "America/New_York", "Europe/London", "UTC"]),
        ],
        icon="clock",
    ),
    "hostname": Component(
        name="hostname",
        display_name="主机名",
        category=ComponentCategory.SYSTEM,
        description="设置系统主机名",
        playbook="hostname",
        options=[
            ComponentOption("hostname", "主机名", "string", required=True),
        ],
        icon="server",
    ),
    "dns": Component(
        name="dns",
        display_name="DNS 配置",
        category=ComponentCategory.SYSTEM,
        description="配置 DNS 服务器",
        playbook="dns",
        options=[
            ComponentOption("dns1", "首选 DNS", "string", default="223.5.5.5"),
            ComponentOption("dns2", "备用 DNS", "string", default="114.114.114.114"),
        ],
        icon="network",
    ),
    "ntp": Component(
        name="ntp",
        display_name="时间同步",
        category=ComponentCategory.SYSTEM,
        description="配置 NTP 时间同步服务",
        playbook="ntp",
        options=[
            ComponentOption("server", "NTP 服务器", "select", default="aliyun",
                options=["aliyun", "tencent", "cn.pool.ntp.org", "time.google.com"]),
        ],
        icon="clock",
    ),
    "locale": Component(
        name="locale",
        display_name="语言/字符集",
        category=ComponentCategory.SYSTEM,
        description="配置系统语言和字符集",
        playbook="locale",
        options=[
            ComponentOption("lang", "语言", "select", default="zh_CN.UTF-8",
                options=["zh_CN.UTF-8", "en_US.UTF-8", "C.UTF-8"]),
        ],
        icon="language",
    ),
    
    # --- 安全配置 ---
    "ssh-hardening": Component(
        name="ssh-hardening",
        display_name="SSH 加固",
        category=ComponentCategory.SYSTEM,
        description="SSH 安全加固配置",
        playbook="ssh-hardening",
        options=[
            ComponentOption("port", "SSH 端口", "number", default="22"),
            ComponentOption("password_auth", "允许密码登录", "select", default="no", options=["yes", "no"]),
            ComponentOption("root_login", "允许 Root 登录", "select", default="no", options=["yes", "no", "prohibit-password"]),
            ComponentOption("max_auth_tries", "最大认证尝试", "number", default="3"),
        ],
        icon="lock",
    ),
    "firewall": Component(
        name="firewall",
        display_name="防火墙",
        category=ComponentCategory.SYSTEM,
        description="配置系统防火墙规则",
        playbook="firewall",
        options=[
            ComponentOption("backend", "防火墙类型", "select", default="ufw",
                options=["ufw", "firewalld", "iptables"]),
            ComponentOption("open_ports", "开放端口", "string", 
                description="逗号分隔，如: 22,80,443"),
            ComponentOption("default_deny", "默认拒绝入站", "boolean", default="true"),
        ],
        icon="shield",
    ),
    "fail2ban": Component(
        name="fail2ban",
        display_name="Fail2ban",
        category=ComponentCategory.SYSTEM,
        description="防暴力破解服务",
        playbook="fail2ban",
        options=[
            ComponentOption("bantime", "封禁时间(秒)", "number", default="3600"),
            ComponentOption("maxretry", "最大重试次数", "number", default="5"),
            ComponentOption("services", "监控服务", "string", default="ssh",
                description="逗号分隔，如: ssh,nginx,mysql"),
        ],
        ports=[22],
        icon="shield",
    ),
    "selinux": Component(
        name="selinux",
        display_name="SELinux 配置",
        category=ComponentCategory.SYSTEM,
        description="配置 SELinux 状态",
        playbook="selinux",
        supported_os=["centos", "rocky", "almalinux", "rhel"],
        options=[
            ComponentOption("state", "SELinux 状态", "select", default="disabled",
                options=["enforcing", "permissive", "disabled"]),
        ],
        icon="lock",
    ),
    
    # --- 性能调优 ---
    "sysctl-tuning": Component(
        name="sysctl-tuning",
        display_name="内核参数优化",
        category=ComponentCategory.SYSTEM,
        description="优化系统内核参数 (TCP、内存、文件句柄)",
        playbook="sysctl-tuning",
        options=[
            ComponentOption("preset", "预设方案", "select", default="general",
                options=["general", "web-server", "database", "high-concurrency"]),
            ComponentOption("tcp_tw_reuse", "TCP TIME_WAIT 复用", "boolean", default="true"),
            ComponentOption("tcp_max_syn_backlog", "TCP SYN 队列", "number", default="65535"),
        ],
        icon="tuning",
    ),
    "ulimit": Component(
        name="ulimit",
        display_name="文件描述符",
        category=ComponentCategory.SYSTEM,
        description="设置系统资源限制 (ulimit)",
        playbook="ulimit",
        options=[
            ComponentOption("nofile", "最大打开文件数", "number", default="65535"),
            ComponentOption("nproc", "最大进程数", "number", default="65535"),
        ],
        icon="tuning",
    ),
    "swap": Component(
        name="swap",
        display_name="Swap 配置",
        category=ComponentCategory.SYSTEM,
        description="配置交换分区",
        playbook="swap",
        options=[
            ComponentOption("action", "操作", "select", default="disable",
                options=["disable", "enable", "create"]),
            ComponentOption("size_gb", "大小 (GB)", "number", default="2",
                description="创建新 Swap 时使用"),
        ],
        icon="memory",
    ),
    
    # --- 系统工具 ---
    "common-tools": Component(
        name="common-tools",
        display_name="常用工具",
        category=ComponentCategory.SYSTEM,
        description="安装常用系统工具包",
        playbook="common-tools",
        options=[
            ComponentOption("packages", "工具包", "select", default="basic",
                options=["basic", "full", "custom"]),
            ComponentOption("custom_packages", "自定义包", "string",
                description="逗号分隔包名"),
        ],
        icon="tool",
    ),
    "node-exporter": Component(
        name="node-exporter",
        display_name="Node Exporter",
        category=ComponentCategory.SYSTEM,
        description="Prometheus 节点监控代理",
        playbook="node-exporter",
        options=[
            ComponentOption("port", "端口", "number", default="9100"),
        ],
        ports=[9100],
        icon="monitor",
    ),
    
    # --- 用户管理 ---
    "create-user": Component(
        name="create-user",
        display_name="创建用户",
        category=ComponentCategory.SYSTEM,
        description="创建系统用户并配置 sudo",
        playbook="create-user",
        options=[
            ComponentOption("username", "用户名", "string", required=True),
            ComponentOption("password", "密码", "password"),
            ComponentOption("sudo_nopasswd", "免密 sudo", "boolean", default="true"),
            ComponentOption("ssh_key", "SSH 公钥", "string"),
        ],
        icon="user",
    ),
    
    # ========================================
    # === DATABASE - 数据库 ===
    # ========================================
    "mysql": Component(
        name="mysql",
        display_name="MySQL",
        category=ComponentCategory.DATABASE,
        description="MySQL 关系型数据库",
        playbook="mysql",
        default_version="8.0",
        versions=["8.0", "5.7"],
        options=[
            ComponentOption("root_password", "Root 密码", "password", required=True),
            ComponentOption("port", "端口", "number", default="3306"),
            ComponentOption("character_set", "字符集", "select", default="utf8mb4", options=["utf8mb4", "utf8"]),
            ComponentOption("max_connections", "最大连接数", "number", default="200"),
        ],
        ports=[3306],
        icon="database",
    ),
    "postgresql": Component(
        name="postgresql",
        display_name="PostgreSQL",
        category=ComponentCategory.DATABASE,
        description="PostgreSQL 高级关系型数据库",
        playbook="postgresql",
        default_version="15",
        versions=["15", "14", "13"],
        options=[
            ComponentOption("postgres_password", "Postgres 密码", "password", required=True),
            ComponentOption("port", "端口", "number", default="5432"),
            ComponentOption("max_connections", "最大连接数", "number", default="100"),
        ],
        ports=[5432],
        icon="database",
    ),
    "redis": Component(
        name="redis",
        display_name="Redis",
        category=ComponentCategory.DATABASE,
        description="Redis 内存数据库/缓存",
        playbook="redis",
        default_version="7",
        versions=["7", "6"],
        options=[
            ComponentOption("port", "端口", "number", default="6379"),
            ComponentOption("password", "密码", "password"),
            ComponentOption("maxmemory", "最大内存 (MB)", "number", default="256"),
            ComponentOption("bind", "绑定地址", "string", default="127.0.0.1"),
        ],
        ports=[6379],
        icon="database",
    ),
    "mongodb": Component(
        name="mongodb",
        display_name="MongoDB",
        category=ComponentCategory.DATABASE,
        description="MongoDB 文档数据库",
        playbook="mongodb",
        default_version="7",
        versions=["7", "6", "5"],
        options=[
            ComponentOption("port", "端口", "number", default="27017"),
            ComponentOption("root_user", "Root 用户名", "string", default="admin"),
            ComponentOption("root_password", "Root 密码", "password", required=True),
        ],
        ports=[27017],
        icon="database",
    ),
    
    # ========================================
    # === MIDDLEWARE - 中间件 ===
    # ========================================
    "nginx": Component(
        name="nginx",
        display_name="Nginx",
        category=ComponentCategory.MIDDLEWARE,
        description="Nginx Web 服务器/反向代理",
        playbook="nginx",
        default_version="latest",
        options=[
            ComponentOption("http_port", "HTTP 端口", "number", default="80"),
            ComponentOption("https_port", "HTTPS 端口", "number", default="443"),
            ComponentOption("worker_processes", "工作进程数", "string", default="auto"),
        ],
        ports=[80, 443],
        icon="server",
    ),
    "apache": Component(
        name="apache",
        display_name="Apache HTTP Server",
        category=ComponentCategory.MIDDLEWARE,
        description="Apache HTTP 服务器",
        playbook="apache",
        default_version="latest",
        options=[
            ComponentOption("http_port", "HTTP 端口", "number", default="80"),
            ComponentOption("https_port", "HTTPS 端口", "number", default="443"),
        ],
        ports=[80, 443],
        icon="server",
    ),
    
    # ========================================
    # === CONTAINER - 容器 ===
    # ========================================
    "docker": Component(
        name="docker",
        display_name="Docker",
        category=ComponentCategory.CONTAINER,
        description="Docker 容器引擎",
        playbook="docker",
        default_version="latest",
        options=[
            ComponentOption("compose", "安装 Docker Compose", "boolean", default="true"),
            ComponentOption("users", "添加用户到 docker 组 (逗号分隔)", "string"),
        ],
        icon="container",
    ),
    "kubernetes": Component(
        name="kubernetes",
        display_name="Kubernetes",
        category=ComponentCategory.CONTAINER,
        description="Kubernetes 容器编排平台",
        playbook="kubernetes",
        default_version="1.28",
        versions=["1.28", "1.27", "1.26"],
        options=[
            ComponentOption("node_type", "节点类型", "select", default="worker", options=["master", "worker"]),
            ComponentOption("pod_cidr", "Pod CIDR", "string", default="10.244.0.0/16"),
            ComponentOption("service_cidr", "Service CIDR", "string", default="10.96.0.0/12"),
        ],
        ports=[6443, 2379, 2380, 10250, 10251, 10252],
        icon="container",
    ),
    
    # ========================================
    # === MESSAGE QUEUE - 消息队列 ===
    # ========================================
    "rabbitmq": Component(
        name="rabbitmq",
        display_name="RabbitMQ",
        category=ComponentCategory.MESSAGE_QUEUE,
        description="RabbitMQ 消息队列",
        playbook="rabbitmq",
        default_version="3.12",
        options=[
            ComponentOption("port", "AMQP 端口", "number", default="5672"),
            ComponentOption("management_port", "管理端口", "number", default="15672"),
            ComponentOption("user", "用户名", "string", default="admin"),
            ComponentOption("password", "密码", "password", required=True),
        ],
        ports=[5672, 15672],
        icon="queue",
    ),
    "kafka": Component(
        name="kafka",
        display_name="Apache Kafka",
        category=ComponentCategory.MESSAGE_QUEUE,
        description="Apache Kafka 分布式消息队列",
        playbook="kafka",
        default_version="3.6",
        dependencies=["zookeeper"],
        options=[
            ComponentOption("port", "端口", "number", default="9092"),
            ComponentOption("broker_id", "Broker ID", "number", default="1"),
        ],
        ports=[9092],
        icon="queue",
    ),
    
    # ========================================
    # === MONITORING - 监控 ===
    # ========================================
    "prometheus": Component(
        name="prometheus",
        display_name="Prometheus",
        category=ComponentCategory.MONITORING,
        description="Prometheus 监控系统",
        playbook="prometheus",
        default_version="latest",
        options=[
            ComponentOption("port", "端口", "number", default="9090"),
            ComponentOption("retention", "数据保留天数", "number", default="15"),
        ],
        ports=[9090],
        icon="chart",
    ),
    "grafana": Component(
        name="grafana",
        display_name="Grafana",
        category=ComponentCategory.MONITORING,
        description="Grafana 可视化面板",
        playbook="grafana",
        default_version="latest",
        options=[
            ComponentOption("port", "端口", "number", default="3000"),
            ComponentOption("admin_password", "Admin 密码", "password", required=True),
        ],
        ports=[3000],
        icon="chart",
    ),
    
    # ========================================
    # === DEVELOPMENT - 开发环境 ===
    # ========================================
    "nodejs": Component(
        name="nodejs",
        display_name="Node.js",
        category=ComponentCategory.DEVELOPMENT,
        description="Node.js JavaScript 运行时",
        playbook="nodejs",
        default_version="20",
        versions=["20", "18", "16"],
        options=[
            ComponentOption("npm_registry", "npm 镜像源", "string"),
            ComponentOption("global_packages", "全局安装包 (逗号分隔)", "string"),
        ],
        icon="code",
    ),
    "python": Component(
        name="python",
        display_name="Python",
        category=ComponentCategory.DEVELOPMENT,
        description="Python 编程语言",
        playbook="python",
        default_version="3.11",
        versions=["3.12", "3.11", "3.10", "3.9"],
        options=[
            ComponentOption("pip_mirror", "pip 镜像源", "string"),
        ],
        icon="code",
    ),
    "golang": Component(
        name="golang",
        display_name="Go",
        category=ComponentCategory.DEVELOPMENT,
        description="Go 编程语言",
        playbook="golang",
        default_version="1.22",
        versions=["1.22", "1.21", "1.20"],
        options=[
            ComponentOption("gopath", "GOPATH", "string", default="/root/go"),
            ComponentOption("goproxy", "Go 代理", "string", default="https://goproxy.cn"),
        ],
        icon="code",
    ),
    "java": Component(
        name="java",
        display_name="Java (OpenJDK)",
        category=ComponentCategory.DEVELOPMENT,
        description="OpenJDK Java 运行时",
        playbook="java",
        default_version="21",
        versions=["21", "17", "11", "8"],
        icon="code",
    ),
    "git": Component(
        name="git",
        display_name="Git",
        category=ComponentCategory.DEVELOPMENT,
        description="Git 版本控制",
        playbook="git",
        default_version="latest",
        icon="code",
    ),
}


def get_component(name: str) -> Optional[Component]:
    """Get component by name."""
    return COMPONENT_REGISTRY.get(name)


def list_components(category: Optional[ComponentCategory] = None) -> List[Component]:
    """List all components, optionally filtered by category."""
    components = list(COMPONENT_REGISTRY.values())
    if category:
        components = [c for c in components if c.category == category]
    return components


def get_categories() -> Dict[str, str]:
    """Get all categories."""
    return {
        ComponentCategory.SYSTEM: "系统基础",
        ComponentCategory.DATABASE: "数据库",
        ComponentCategory.MIDDLEWARE: "中间件",
        ComponentCategory.MESSAGE_QUEUE: "消息队列",
        ComponentCategory.CONTAINER: "容器",
        ComponentCategory.MONITORING: "监控",
        ComponentCategory.DEVELOPMENT: "开发环境",
        ComponentCategory.OTHER: "其他",
    }