/**
 * Job card component displaying individual job status and progress.
 */

import React from 'react';
import { Card, Progress, Tag, Button, Typography, Space, Alert } from 'antd';
import {
  DownloadOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { Job, JobStatus } from '../types';

const { Text, Title } = Typography;

interface JobCardProps {
  job: Job;
}

const API_URL = 'http://localhost:8000';

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const getStatusTag = () => {
    switch (job.status) {
      case JobStatus.QUEUED:
        return (
          <Tag icon={<ClockCircleOutlined />} color="default">
            排队中
          </Tag>
        );
      case JobStatus.EXTRACTING_AUDIO:
        return (
          <Tag icon={<SyncOutlined spin />} color="processing">
            提取音频
          </Tag>
        );
      case JobStatus.TRANSCRIBING:
        return (
          <Tag icon={<SyncOutlined spin />} color="processing">
            转录中
          </Tag>
        );
      case JobStatus.COMPLETED:
        return (
          <Tag icon={<CheckCircleOutlined />} color="success">
            已完成
          </Tag>
        );
      case JobStatus.FAILED:
        return (
          <Tag icon={<CloseCircleOutlined />} color="error">
            失败
          </Tag>
        );
      default:
        return <Tag>{job.status}</Tag>;
    }
  };

  const getProgressStatus = () => {
    if (job.status === JobStatus.COMPLETED) return 'success';
    if (job.status === JobStatus.FAILED) return 'exception';
    return 'active';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  const handleDownload = () => {
    window.open(`${API_URL}/api/download/${job.id}`, '_blank');
  };

  return (
    <Card
      style={{ marginBottom: 16 }}
      title={
        <Space>
          <Title level={5} style={{ margin: 0 }}>
            {job.filename}
          </Title>
          {getStatusTag()}
        </Space>
      }
      extra={
        job.status === JobStatus.COMPLETED && (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleDownload}
          >
            下载转录文本
          </Button>
        )
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div>
          <Text type="secondary">文件大小：</Text>
          <Text>{formatFileSize(job.file_size)}</Text>
          <Text type="secondary" style={{ marginLeft: 16 }}>
            创建时间：
          </Text>
          <Text>{formatDate(job.created_at)}</Text>
        </div>

        {job.status !== JobStatus.QUEUED && (
          <>
            <div>
              <Text strong>{job.current_stage}</Text>
              <Progress
                percent={Math.round(job.progress)}
                status={getProgressStatus()}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </div>
          </>
        )}

        {job.status === JobStatus.COMPLETED && job.completed_at && (
          <Alert
            message="转录完成"
            description={`完成时间：${formatDate(job.completed_at)}`}
            type="success"
            showIcon
          />
        )}

        {job.status === JobStatus.FAILED && job.error_message && (
          <Alert
            message="处理失败"
            description={job.error_message}
            type="error"
            showIcon
          />
        )}
      </Space>
    </Card>
  );
};
