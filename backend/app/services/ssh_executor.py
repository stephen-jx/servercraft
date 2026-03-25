"""SSH Executor for remote server operations."""
import asyncio
import asyncssh
from typing import Optional, Tuple, List, Callable
from loguru import logger
from dataclasses import dataclass

from ..core.config import settings


@dataclass
class SSHResult:
    """SSH command result."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str


class SSHExecutor:
    """SSH executor for remote server operations."""
    
    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        ssh_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh_key = ssh_key
        self.timeout = timeout
        self._conn: Optional[asyncssh.SSHClientConnection] = None
    
    async def connect(self) -> bool:
        """Connect to the server."""
        try:
            connect_kwargs = {
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "known_hosts": None,  # Disable host key checking
            }
            
            if self.password:
                connect_kwargs["password"] = self.password
            elif self.ssh_key:
                connect_kwargs["client_keys"] = [self.ssh_key]
            
            self._conn = await asyncio.wait_for(
                asyncssh.connect(**connect_kwargs),
                timeout=self.timeout
            )
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {self.host}")
            raise ConnectionError(f"Connection timeout to {self.host}")
        except asyncssh.AuthenticationError as e:
            logger.error(f"Authentication failed for {self.host}: {e}")
            raise ConnectionError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"Connection failed to {self.host}: {e}")
            raise ConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None
            logger.info(f"Disconnected from {self.host}")
    
    async def execute(self, command: str, timeout: int = 300) -> SSHResult:
        """Execute a command on the server."""
        if not self._conn:
            raise ConnectionError("Not connected")
        
        try:
            result = await asyncio.wait_for(
                self._conn.run(command),
                timeout=timeout
            )
            
            return SSHResult(
                success=result.exit_status == 0,
                exit_code=result.exit_status,
                stdout=result.stdout,
                stderr=result.stderr
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Command timeout: {command}")
            return SSHResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Command timeout"
            )
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return SSHResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e)
            )
    
    async def execute_streaming(
        self,
        command: str,
        output_callback: Callable[[str], None],
        timeout: int = 3600
    ) -> SSHResult:
        """Execute a command with streaming output."""
        if not self._conn:
            raise ConnectionError("Not connected")
        
        stdout_lines = []
        stderr_lines = []
        
        try:
            proc = await asyncio.wait_for(
                self._conn.create_process(command),
                timeout=timeout
            )
            
            async def read_stdout():
                async for line in proc.stdout:
                    stdout_lines.append(line)
                    output_callback(f"[OUT] {line}")
            
            async def read_stderr():
                async for line in proc.stderr:
                    stderr_lines.append(line)
                    output_callback(f"[ERR] {line}")
            
            # Read both streams concurrently
            await asyncio.gather(read_stdout(), read_stderr())
            
            await proc.wait()
            
            return SSHResult(
                success=proc.exit_status == 0,
                exit_code=proc.exit_status or -1,
                stdout="".join(stdout_lines),
                stderr="".join(stderr_lines)
            )
            
        except asyncio.TimeoutError:
            return SSHResult(
                success=False,
                exit_code=-1,
                stdout="".join(stdout_lines),
                stderr="Command timeout"
            )
        except Exception as e:
            return SSHResult(
                success=False,
                exit_code=-1,
                stdout="".join(stdout_lines),
                stderr=str(e)
            )
    
    async def detect_os(self) -> Tuple[str, str, str]:
        """Detect the OS type, version, and architecture."""
        if not self._conn:
            raise ConnectionError("Not connected")
        
        # Detect OS
        result = await self.execute("cat /etc/os-release 2>/dev/null || cat /etc/redhat-release 2>/dev/null")
        
        os_type = "unknown"
        os_version = "unknown"
        
        if result.success:
            output = result.stdout.lower()
            if "ubuntu" in output:
                os_type = "ubuntu"
            elif "debian" in output:
                os_type = "debian"
            elif "centos" in output:
                os_type = "centos"
            elif "rocky" in output:
                os_type = "rocky"
            elif "alma" in output:
                os_type = "almalinux"
            elif "red hat" in output or "rhel" in output:
                os_type = "rhel"
            
            # Extract version
            import re
            version_match = re.search(r'version_id="?(\d+\.?\d*)"?', output)
            if version_match:
                os_version = version_match.group(1)
        
        # Detect architecture
        result = await self.execute("uname -m")
        arch = result.stdout.strip() if result.success else "unknown"
        
        return os_type, os_version, arch
    
    async def get_system_info(self) -> dict:
        """Get system information."""
        if not self._conn:
            raise ConnectionError("Not connected")
        
        os_type, os_version, arch = await self.detect_os()
        
        # Get CPU cores
        result = await self.execute("nproc")
        cpu_cores = int(result.stdout.strip()) if result.success else 0
        
        # Get memory
        result = await self.execute("free -m | awk '/Mem:/ {print $2}'")
        memory_mb = int(result.stdout.strip()) if result.success else 0
        
        # Get disk
        result = await self.execute("df -BG / | awk 'NR==2 {print $2}' | tr -d 'G'")
        disk_gb = int(result.stdout.strip()) if result.success else 0
        
        return {
            "os_type": os_type,
            "os_version": os_version,
            "arch": arch,
            "cpu_cores": cpu_cores,
            "memory_mb": memory_mb,
            "disk_gb": disk_gb
        }
    
    async def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        result = await self.execute(f"test -f {path}")
        return result.success
    
    async def directory_exists(self, path: str) -> bool:
        """Check if a directory exists."""
        result = await self.execute(f"test -d {path}")
        return result.success
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to the server."""
        if not self._conn:
            raise ConnectionError("Not connected")
        
        try:
            async with asyncssh.sftp(self._conn) as sftp:
                await sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    async def upload_content(self, content: str, remote_path: str) -> bool:
        """Upload content as a file."""
        if not self._conn:
            raise ConnectionError("Not connected")
        
        try:
            async with asyncssh.sftp(self._conn) as sftp:
                async with sftp.open(remote_path, 'w') as f:
                    await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Upload content failed: {e}")
            return False
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()