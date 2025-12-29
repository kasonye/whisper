/**
 * Main application component.
 */

import React from 'react';
import { Layout, Typography, Space, Badge, Divider } from 'antd';
import { VideoUpload } from './components/VideoUpload';
import { JobQueue } from './components/JobQueue';
import { useWebSocket } from './hooks/useWebSocket';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

const WS_URL = 'ws://localhost:8000/ws';

const App: React.FC = () => {
  const { jobs, isConnected } = useWebSocket(WS_URL);

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header style={{ background: '#fff', padding: '0 50px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2} style={{ margin: '16px 0', color: '#1890ff' }}>
            视频转录系统
          </Title>
          <Space>
            <Badge
              status={isConnected ? 'success' : 'error'}
              text={
                <Text strong>
                  {isConnected ? '已连接' : '未连接'}
                </Text>
              }
            />
          </Space>
        </div>
      </Header>

      <Content style={{ padding: '50px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <VideoUpload />
            <Divider />
            <JobQueue jobs={jobs} />
          </Space>
        </div>
      </Content>

      <Footer style={{ textAlign: 'center', background: '#fff' }}>
        <Text type="secondary">
          视频转录系统 ©2024 | 基于 FastAPI + React + Whisper
        </Text>
      </Footer>
    </Layout>
  );
};

export default App;
