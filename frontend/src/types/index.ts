/**
 * TypeScript type definitions for the application.
 */

export enum JobStatus {
  QUEUED = 'queued',
  EXTRACTING_AUDIO = 'extracting_audio',
  TRANSCRIBING = 'transcribing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface Job {
  id: string;
  filename: string;
  file_size: number;
  status: JobStatus;
  progress: number; // 0-100
  current_stage: string;
  created_at: string;
  completed_at?: string;
  error_message?: string;
  video_path: string;
  audio_path?: string;
  transcript_path?: string;
}

export interface ProgressUpdate {
  job_id: string;
  status: JobStatus;
  progress: number;
  current_stage: string;
  message: string;
}
