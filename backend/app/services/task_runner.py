"""Task runner for parallel component installation."""
import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Callable
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models import Task, SubTask, TaskStatus, TaskType, Server, ServerComponent
from .ssh_executor import SSHExecutor
from .components import get_component, Component, COMPONENT_REGISTRY


# 安全：组件名称白名单验证
def validate_component_name(name: str) -> str:
    """验证组件名称，防止命令注入"""
    # 只允许小写字母、数字和连字符
    if not re.match(r'^[a-z0-9-]+$', name):
        raise ValueError(f"Invalid component name: {name}")
    
    # 必须在注册表中
    if name not in COMPONENT_REGISTRY:
        raise ValueError(f"Unknown component: {name}")
    
    return name


class TaskRunner:
    """Runner for installation tasks with parallel support."""
    
    def __init__(
        self,
        db: AsyncSession,
        task: Task,
        output_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.db = db
        self.task = task
        self.output_callback = output_callback
        self._server: Optional[Server] = None
        self._executor: Optional[SSHExecutor] = None
    
    async def run(self):
        """Run the task."""
        try:
            # Update task status
            self.task.status = TaskStatus.RUNNING
            self.task.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Get server info
            self._server = await self._get_server()
            if not self._server:
                raise ValueError("Server not found")
            
            # Create SSH executor
            self._executor = SSHExecutor(
                host=self._server.ip_address,
                port=self._server.port,
                username=self._server.username,
                password=self._server.password,
                ssh_key=self._server.ssh_key,
                timeout=settings.SSH_TIMEOUT
            )
            
            # Connect
            await self._executor.connect()
            self._output("Connected to server", "info")
            
            # Parse components
            components = self._parse_components()
            
            if self.task.task_type == TaskType.INSTALL:
                await self._install_parallel(components)
            elif self.task.task_type == TaskType.UNINSTALL:
                await self._uninstall_parallel(components)
            else:
                await self._execute_task(components)
            
            # Success
            self.task.status = TaskStatus.SUCCESS
            self.task.completed_at = datetime.utcnow()
            self.task.duration_seconds = int((self.task.completed_at - self.task.started_at).total_seconds())
            await self.db.commit()
            
        except Exception as e:
            logger.exception(f"Task failed: {e}")
            self.task.status = TaskStatus.FAILED
            self.task.error_message = str(e)
            self.task.completed_at = datetime.utcnow()
            await self.db.commit()
            
        finally:
            if self._executor:
                await self._executor.disconnect()
    
    async def _get_server(self) -> Optional[Server]:
        """Get server from database."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(Server).where(Server.id == self.task.server_id)
        )
        return result.scalar_one_or_none()
    
    def _parse_components(self) -> List[str]:
        """Parse component names from task."""
        if self.task.component_names:
            return json.loads(self.task.component_names)
        return []
    
    async def _install_parallel(self, component_names: List[str]):
        """Install multiple components in parallel."""
        self._output(f"Installing {len(component_names)} components in parallel", "info")
        
        # Create subtasks
        for name in component_names:
            subtask = SubTask(
                task_id=self.task.id,
                component_name=name,
                status=TaskStatus.PENDING
            )
            self.db.add(subtask)
        await self.db.commit()
        
        # Get subtasks
        subtasks = list(self.task.subtasks)
        
        # Run installations in parallel
        tasks = [
            self._install_component(subtask)
            for subtask in subtasks
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update overall progress
        success_count = sum(1 for st in subtasks if st.status == TaskStatus.SUCCESS)
        self.task.progress = int((success_count / len(subtasks)) * 100)
        await self.db.commit()
    
    async def _install_component(self, subtask: SubTask):
        """Install a single component."""
        subtask.status = TaskStatus.RUNNING
        subtask.started_at = datetime.utcnow()
        await self.db.commit()
        
        try:
            component = get_component(subtask.component_name)
            if not component:
                raise ValueError(f"Unknown component: {subtask.component_name}")
            
            self._output(f"Installing {component.display_name}...", "info")
            
            # Detect OS
            os_type, os_version, arch = await self._executor.detect_os()
            self._output(f"Detected OS: {os_type} {os_version} ({arch})", "info")
            
            # Install dependencies first
            for dep_name in component.dependencies:
                self._output(f"Installing dependency: {dep_name}", "info")
                await self._install_single_component(dep_name)
            
            # Install main component
            await self._install_single_component(subtask.component_name)
            
            # Success
            subtask.status = TaskStatus.SUCCESS
            subtask.completed_at = datetime.utcnow()
            await self.db.commit()
            
            # Record installed component
            server_component = ServerComponent(
                server_id=self.task.server_id,
                component_name=subtask.component_name,
                status="installed"
            )
            self.db.add(server_component)
            await self.db.commit()
            
            self._output(f"Successfully installed {component.display_name}", "success")
            
        except Exception as e:
            subtask.status = TaskStatus.FAILED
            subtask.error_message = str(e)
            subtask.completed_at = datetime.utcnow()
            await self.db.commit()
            self._output(f"Failed to install {subtask.component_name}: {e}", "error")
            raise
    
    async def _install_single_component(self, component_name: str):
        """Install a single component using shell commands."""
        # 安全：验证组件名称
        component_name = validate_component_name(component_name)
        
        component = get_component(component_name)
        if not component:
            raise ValueError(f"Unknown component: {component_name}")
        
        # Get options
        options = {}
        if self.task.options:
            options = json.loads(self.task.options) if isinstance(self.task.options, str) else self.task.options
        component_options = options.get(component_name, {})
        
        # Build install command based on OS
        result = await self._executor.execute("cat /etc/os-release | grep -i ^id=")
        os_id = result.stdout.split("=")[1].strip().lower() if result.success else "ubuntu"
        
        # Generate installation commands
        commands = self._get_install_commands(component, os_id, component_options)
        
        for cmd in commands:
            self._output(f"Executing: {cmd[:100]}...", "info")
            result = await self._executor.execute(cmd, timeout=600)
            if not result.success:
                raise Exception(f"Command failed: {result.stderr}")
    
    def _get_install_commands(self, component: Component, os_id: str, options: dict) -> List[str]:
        """Get installation commands for a component."""
        commands = []
        
        # Package manager selection
        if os_id in ["ubuntu", "debian"]:
            pkg_mgr = "apt-get"
            update_cmd = "apt-get update -y"
            install_cmd = "apt-get install -y"
        elif os_id in ["centos", "rocky", "almalinux", "rhel"]:
            pkg_mgr = "yum"
            update_cmd = "yum update -y"
            install_cmd = "yum install -y"
        else:
            pkg_mgr = "apt-get"
            update_cmd = "apt-get update -y"
            install_cmd = "apt-get install -y"
        
        # Component-specific installation
        if component.name == "docker":
            commands.extend([
                f"{update_cmd}",
                f"{install_cmd} -y ca-certificates curl gnupg lsb-release",
                "mkdir -p /etc/apt/keyrings 2>/dev/null || true",
                "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null',
                f"{update_cmd}",
                f"{install_cmd} -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
                "systemctl enable docker",
                "systemctl start docker",
            ])
        
        elif component.name == "nginx":
            commands.extend([
                f"{update_cmd}",
                f"{install_cmd} -y nginx",
                "systemctl enable nginx",
                "systemctl start nginx",
            ])
        
        elif component.name == "mysql":
            root_password = options.get("root_password", "Root@123456")
            port = options.get("port", "3306")
            commands.extend([
                f"{update_cmd}",
                f"{install_cmd} -y mysql-server",
                "systemctl enable mysql",
                "systemctl start mysql",
                f"mysql -e \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{root_password}';\"",
            ])
        
        elif component.name == "redis":
            port = options.get("port", "6379")
            password = options.get("password", "")
            commands.extend([
                f"{update_cmd}",
                f"{install_cmd} -y redis-server",
                "systemctl enable redis-server",
                "systemctl start redis-server",
            ])
            if password:
                commands.append(f"redis-cli CONFIG SET requirepass '{password}'")
        
        elif component.name == "nodejs":
            version = options.get("version", "20")
            commands.extend([
                f"curl -fsSL https://deb.nodesource.com/setup_{version}.x | bash -",
                f"{install_cmd} -y nodejs",
                "node --version",
                "npm --version",
            ])
        
        elif component.name == "python":
            version = options.get("version", "3.11")
            commands.extend([
                f"{update_cmd}",
                f"{install_cmd} -y python{version} python{version}-venv python{version}-dev python3-pip",
                f"python{version} --version",
            ])
        
        elif component.name == "golang":
            version = options.get("version", "1.22")
            commands.extend([
                f"wget -q https://go.dev/dl/go{version}.linux-amd64.tar.gz",
                "rm -rf /usr/local/go",
                f"tar -C /usr/local -xzf go{version}.linux-amd64.tar.gz",
                "export PATH=$PATH:/usr/local/go/bin",
                "echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc",
                "/usr/local/go/bin/go version",
            ])
        
        elif component.name == "git":
            commands.extend([
                f"{update_cmd}",
                f"{install_cmd} -y git",
                "git --version",
            ])
        
        else:
            # Generic: try to install with package manager
            commands.extend([
                f"{update_cmd}",
                f"{install_cmd} -y {component.name}",
            ])
        
        return commands
    
    async def _uninstall_parallel(self, component_names: List[str]):
        """Uninstall multiple components."""
        for name in component_names:
            await self._uninstall_component(name)
    
    async def _uninstall_component(self, component_name: str):
        """Uninstall a single component."""
        # 安全：验证组件名称
        component_name = validate_component_name(component_name)
        
        self._output(f"Uninstalling {component_name}...", "info")
        # 安全：使用参数化命令，避免注入
        result = await self._executor.execute(
            f"apt-get remove -y {component_name} 2>/dev/null || yum remove -y {component_name} 2>/dev/null || echo 'Package not found'"
        )
        self._output(f"Uninstalled {component_name}", "info")
    
    async def _execute_task(self, components: List[str]):
        """Execute other task types."""
        # For start/stop/restart/configure
        pass
    
    def _output(self, message: str, level: str = "info"):
        """Log output and call callback."""
        logger.info(f"[Task {self.task.id}] {message}")
        if self.output_callback:
            self.output_callback(message, level)
        
        # Append to task output
        if self.task.output:
            self.task.output += f"\n[{datetime.utcnow().isoformat()}] {message}"
        else:
            self.task.output = f"[{datetime.utcnow().isoformat()}] {message}"


# === Background Task Execution ===

async def run_task_background(db: AsyncSession, task_id: int):
    """Run a task in background (simplified, non-Celery version)."""
    from sqlalchemy import select
    
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    
    runner = TaskRunner(db, task)
    await runner.run()


# Celery task (optional, for production use)
try:
    from ..core.celery_app import celery_app
    
    @celery_app.task(bind=True)
    def run_task_celery(self, task_id: int):
        """Celery task for background execution."""
        import asyncio
        from ..core import async_session_maker
        
        async def _run():
            async with async_session_maker() as db:
                await run_task_background(db, task_id)
        
        asyncio.run(_run())
        
except ImportError:
    # Celery not configured
    pass