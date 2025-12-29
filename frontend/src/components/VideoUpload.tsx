/**
 * Video upload component with drag-and-drop support.
 */

import React, { useState } from 'react';
import { Upload, Button, message, Card, Typography } from 'antd';
import { InboxOutlined, UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import axios from 'axios';

const { Dragger } = Upload;
const { Title, Text } = Typography;

const API_URL = 'http://localhost:8000';

export const VideoUpload: React.FC = () => {
  const [uploading, setUploading] = useState(false);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.mp4,.avi,.mkv,.mov,.webm,.flv,.wmv',
    showUploadList: true,
    beforeUpload: (file) => {
      const isVideo = [
        'video/mp4',
        'video/x-msvideo',
        'video/x-matroska',
        'video/quicktime',
        'video/webm',
        'video/x-flv',
        'video/x-ms-wmv',
      ].includes(file.type) || file.name.match(/\.(mp4|avi|mkv|mov|webm|flv|wmv)$/i);

      if (!isVideo) {
        message.error('只能上传视频文件！');
        return Upload.LIST_IGNORE;
      }

      const isLt2G = file.size / 1024 / 1024 / 1024 < 2;
      if (!isLt2G) {
        message.error('视频文件必须小于 2GB！');
        return Upload.LIST_IGNORE;
      }

      return true; // Allow upload with customRequest
    },
    customRequest: async ({ file, onSuccess, onError, onProgress }) => {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file as File);

      try {
        const response = await axios.post(`${API_URL}/api/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percent = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            onProgress?.({ percent });
          },
        });

        message.success(`${(file as File).name} 上传成功！已加入处理队列。`);
        onSuccess?.(response.data);
      } catch (error: any) {
        console.error('Upload error:', error);
        const errorMsg = error.response?.data?.detail || '上传失败';
        message.error(errorMsg);
        onError?.(error);
      } finally {
        setUploading(false);
      }
    },
    onDrop(e) {
      console.log('Dropped files', e.dataTransfer.files);
    },
  };

  return (
    <Card>
      <Title level={3}>上传视频</Title>
      <Text type="secondary">
        支持的格式：MP4, AVI, MKV, MOV, WEBM, FLV, WMV（最大 2GB）
      </Text>
      <div style={{ marginTop: 16 }}>
        <Dragger {...uploadProps} disabled={uploading}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽视频文件到此区域上传</p>
          <p className="ant-upload-hint">
            上传后将自动提取音频并使用 Whisper 进行转录
          </p>
        </Dragger>
      </div>
    </Card>
  );
};
