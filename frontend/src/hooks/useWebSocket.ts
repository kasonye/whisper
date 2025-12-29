/**
 * Custom hook for WebSocket connection and job updates.
 */

import { useEffect, useRef, useState } from 'react';
import { Job } from '../types';

export const useWebSocket = (url: string) => {
  const [jobs, setJobs] = useState<Map<string, Job>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const connect = () => {
      console.log('Connecting to WebSocket:', url);
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.current.onmessage = (event) => {
        try {
          // Skip non-JSON messages (like "pong")
          if (typeof event.data === 'string' && !event.data.startsWith('{')) {
            console.log('Received non-JSON message:', event.data);
            return;
          }

          const job: Job = JSON.parse(event.data);
          console.log('Received job update:', job.id, job.status, job.progress);
          setJobs((prev) => {
            const newJobs = new Map(prev);
            newJobs.set(job.id, job);
            return newJobs;
          });
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(connect, 3000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  // Send ping to keep connection alive
  useEffect(() => {
    if (!isConnected || !ws.current) return;

    const pingInterval = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send('ping');
      }
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected]);

  return {
    jobs: Array.from(jobs.values()).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    ),
    isConnected,
  };
};
