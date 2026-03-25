import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Card, Tag, Button, Space, Progress, message } from 'antd'
import { ReloadOutlined, EyeOutlined } from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

interface Task {
  id: number
  task_type: string
  server_id: number
  status: string
  progress: number
  component_names: string[]
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  error_message?: string
  created_at: string
}

interface Server {
  id: number
  name: string
  ip_address: string
}

const TasksPage = () => {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState<Task[]>([])
  const [servers, setServers] = useState<Server[]>([])
  const [loading, setLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [tasksRes, serversRes] = await Promise.all([
        axios.get('/api/v1/tasks'),
        axios.get('/api/v1/servers'),
      ])
      setTasks(tasksRes.data.items || [])
      setServers(serversRes.data.items || [])
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Auto refresh every 5 seconds for running tasks
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const getServerName = (serverId: number) => {
    const server = servers.find(s => s.id === serverId)
    return server ? `${server.name} (${server.ip_address})` : `Server #${serverId}`
  }

  const statusColors: Record<string, string> = {
    pending: 'default',
    running: 'processing',
    success: 'success',
    failed: 'error',
    cancelled: 'warning',
  }

  const statusText: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消',
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'install' ? 'blue' : 'orange'}>
          {type === 'install' ? '安装' : '卸载'}
        </Tag>
      ),
    },
    {
      title: '服务器',
      dataIndex: 'server_id',
      key: 'server',
      render: (serverId: number) => getServerName(serverId),
    },
    {
      title: '组件',
      dataIndex: 'component_names',
      key: 'components',
      render: (names: string[]) => (
        <Space size={4} wrap>
          {names?.map(name => (
            <Tag key={name}>{name}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: Task) => (
        <Progress
          percent={progress || 0}
          size="small"
          status={record.status === 'running' ? 'active' : undefined}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={statusColors[status]}>{statusText[status] || status}</Tag>
      ),
    },
    {
      title: '耗时',
      dataIndex: 'duration_seconds',
      key: 'duration',
      width: 100,
      render: (seconds: number) => {
        if (!seconds) return '-'
        if (seconds < 60) return `${seconds}s`
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}m ${secs}s`
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Task) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/tasks/${record.id}`)}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <Card
      title="任务列表"
      extra={
        <Button icon={<ReloadOutlined />} onClick={fetchData}>
          刷新
        </Button>
      }
    >
      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
      />
    </Card>
  )
}

export default TasksPage