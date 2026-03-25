import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Progress, Button, Space, message, Popconfirm, Typography } from 'antd'
import { ArrowLeftOutlined, ReloadOutlined, StopOutlined } from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

const { Title, Text } = Typography

interface Task {
  id: number
  task_type: string
  server_id: number
  component_names: string[]
  status: string
  progress: number
  current_step?: string
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  output?: string
  error_message?: string
  subtasks: SubTask[]
  created_at: string
}

interface SubTask {
  id: number
  component_name: string
  status: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

interface Server {
  id: number
  name: string
  ip_address: string
}

const TaskDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<Task | null>(null)
  const [server, setServer] = useState<Server | null>(null)
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const logRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const fetchTask = async () => {
    if (!id) return
    setLoading(true)
    try {
      const res = await axios.get(`/api/v1/tasks/${id}`)
      setTask(res.data)

      // Parse output into lines
      if (res.data.output) {
        setLogs(res.data.output.split('\n'))
      }

      // Fetch server info
      if (res.data.server_id) {
        const serverRes = await axios.get(`/api/v1/servers/${res.data.server_id}`)
        setServer(serverRes.data)
      }
    } catch (error) {
      message.error('获取任务详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTask()

    // Connect WebSocket for real-time updates
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/tasks/ws/${id}`)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.output) {
        setLogs(prev => [...prev, data.output])
      }
      if (data.status) {
        fetchTask()
      }
    }
    wsRef.current = ws

    // Auto refresh for running tasks
    const interval = setInterval(() => {
      if (task?.status === 'running' || task?.status === 'pending') {
        fetchTask()
      }
    }, 3000)

    return () => {
      ws.close()
      clearInterval(interval)
    }
  }, [id])

  // Auto scroll to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  const handleCancel = async () => {
    try {
      await axios.post(`/api/v1/tasks/${id}/cancel`)
      message.success('任务已取消')
      fetchTask()
    } catch (error) {
      message.error('取消失败')
    }
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

  if (!task) {
    return <Card loading={loading} />
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tasks')}>
          返回列表
        </Button>
        <Button icon={<ReloadOutlined />} onClick={fetchTask}>
          刷新
        </Button>
        {(task.status === 'running' || task.status === 'pending') && (
          <Popconfirm title="确定取消任务?" onConfirm={handleCancel}>
            <Button danger icon={<StopOutlined />}>
              取消任务
            </Button>
          </Popconfirm>
        )}
      </Space>

      <Card title="任务信息" style={{ marginBottom: 16 }}>
        <Descriptions column={3}>
          <Descriptions.Item label="任务ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="类型">
            <Tag color={task.task_type === 'install' ? 'blue' : 'orange'}>
              {task.task_type === 'install' ? '安装' : '卸载'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColors[task.status]}>{statusText[task.status]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="服务器">
            {server ? `${server.name} (${server.ip_address})` : `Server #${task.server_id}`}
          </Descriptions.Item>
          <Descriptions.Item label="进度">
            <Progress
              percent={task.progress || 0}
              size="small"
              status={task.status === 'running' ? 'active' : undefined}
              style={{ width: 150 }}
            />
          </Descriptions.Item>
          <Descriptions.Item label="耗时">
            {task.duration_seconds
              ? `${Math.floor(task.duration_seconds / 60)}m ${task.duration_seconds % 60}s`
              : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="开始时间">
            {task.started_at ? dayjs(task.started_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {task.completed_at ? dayjs(task.completed_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="子任务" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {task.subtasks?.map(st => (
            <Card
              key={st.id}
              size="small"
              style={{ width: 200 }}
              title={st.component_name}
            >
              <Tag color={statusColors[st.status]}>{statusText[st.status]}</Tag>
              {st.error_message && (
                <Text type="danger" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                  {st.error_message}
                </Text>
              )}
            </Card>
          ))}
        </div>
      </Card>

      <Card title="执行日志">
        <div
          ref={logRef}
          className="terminal"
          style={{
            minHeight: 300,
            maxHeight: 500,
            overflow: 'auto',
            backgroundColor: '#1a1a1a',
            padding: 16,
            borderRadius: 8,
          }}
        >
          {logs.length === 0 ? (
            <div style={{ color: '#666' }}>暂无日志</div>
          ) : (
            logs.map((line, idx) => (
              <div
                key={idx}
                className={`terminal-line ${
                  line.includes('[ERR]') || line.includes('error') || line.includes('Error')
                    ? 'error'
                    : line.includes('[OUT]') || line.includes('Successfully')
                    ? 'success'
                    : 'info'
                }`}
                style={{
                  fontFamily: 'Monaco, Menlo, Ubuntu Mono, monospace',
                  fontSize: 13,
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  color: line.includes('[ERR]') || line.includes('error') || line.includes('Error')
                    ? '#ff6b6b'
                    : line.includes('Successfully') || line.includes('Success')
                    ? '#69db7c'
                    : '#00ff00',
                }}
              >
                {line}
              </div>
            ))
          )}
        </div>
      </Card>

      {task.error_message && (
        <Card title="错误信息" style={{ marginTop: 16 }}>
          <Text type="danger">{task.error_message}</Text>
        </Card>
      )}
    </div>
  )
}

export default TaskDetailPage