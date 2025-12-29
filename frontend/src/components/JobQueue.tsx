/**
 * Job queue component displaying all jobs.
 */

import React, { useState } from 'react';
import { Card, Typography, Empty, Radio, Space } from 'antd';
import { Job, JobStatus } from '../types';
import { JobCard } from './JobCard';

const { Title } = Typography;

interface JobQueueProps {
  jobs: Job[];
}

type FilterType = 'all' | 'processing' | 'completed' | 'failed';

export const JobQueue: React.FC<JobQueueProps> = ({ jobs }) => {
  const [filter, setFilter] = useState<FilterType>('all');

  const filterJobs = (jobs: Job[]): Job[] => {
    switch (filter) {
      case 'processing':
        return jobs.filter(
          (job) =>
            job.status === JobStatus.QUEUED ||
            job.status === JobStatus.EXTRACTING_AUDIO ||
            job.status === JobStatus.TRANSCRIBING
        );
      case 'completed':
        return jobs.filter((job) => job.status === JobStatus.COMPLETED);
      case 'failed':
        return jobs.filter((job) => job.status === JobStatus.FAILED);
      default:
        return jobs;
    }
  };

  const filteredJobs = filterJobs(jobs);

  const getJobCount = (type: FilterType): number => {
    return filterJobs(jobs).length;
  };

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={3} style={{ margin: 0 }}>
            处理队列 ({jobs.length})
          </Title>
          <Radio.Group
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value="all">
              全部 ({jobs.length})
            </Radio.Button>
            <Radio.Button value="processing">
              处理中 (
              {
                jobs.filter(
                  (j) =>
                    j.status === JobStatus.QUEUED ||
                    j.status === JobStatus.EXTRACTING_AUDIO ||
                    j.status === JobStatus.TRANSCRIBING
                ).length
              }
              )
            </Radio.Button>
            <Radio.Button value="completed">
              已完成 ({jobs.filter((j) => j.status === JobStatus.COMPLETED).length})
            </Radio.Button>
            <Radio.Button value="failed">
              失败 ({jobs.filter((j) => j.status === JobStatus.FAILED).length})
            </Radio.Button>
          </Radio.Group>
        </div>

        {filteredJobs.length === 0 ? (
          <Empty
            description={
              filter === 'all'
                ? '暂无任务，请上传视频文件'
                : `暂无${
                    filter === 'processing'
                      ? '处理中'
                      : filter === 'completed'
                      ? '已完成'
                      : '失败'
                  }的任务`
            }
          />
        ) : (
          <div>
            {filteredJobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </Space>
    </Card>
  );
};
