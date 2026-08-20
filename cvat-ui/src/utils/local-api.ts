// SPDX-License-Identifier: MIT

export interface WorkspaceEntry {
    path: string;
    kind: 'directory' | 'image' | 'video' | 'archive';
}

export interface VideoMetadata {
    path: string;
    duration: number;
    fps: number;
    frame_count: number;
    width: number;
    height: number;
}

export interface ExtractionParameters {
    path: string;
    start_time: number;
    end_time: number;
    interval: number;
    strength: 'low' | 'medium' | 'high';
    overwrite?: boolean;
}

export interface ExtractionResult {
    source_count: number;
    exact_duplicates: number;
    similar_skipped: number;
    kept_count: number;
    output_path: string;
}

export interface ExtractionStatus {
    id: string;
    status: string;
    progress: number;
    result?: ExtractionResult;
    error?: string;
}

export interface AppendableTask {
    id: number;
    name: string;
    size: number;
}

export interface TaskImageAppendResult {
    task_id: number;
    added_count: number;
    total_count: number;
}

export interface PackageImportStatus {
    id: string;
    status: string;
    progress: number;
    message?: string;
    result?: { task_id: number };
    error?: string;
}

export type FrameReviewStatus = 'unreviewed' | 'annotated' | 'empty';

export interface FrameStatus {
    status: FrameReviewStatus;
}

export interface TaskReviewSummary {
    total: number;
    reviewed: number;
    annotated: number;
    empty: number;
    unreviewed: number;
}

export const FRAME_STATUS_UPDATED_EVENT = 'cvat-local-frame-status-updated';
export const YOLO26_PACKAGE_FORMAT = 'YOLO26 Detect 标注包';

export class LocalAPIError extends Error {
    public readonly status: number;

    public readonly code?: string;

    public constructor(status: number, message: string, code?: string) {
        super(message);
        this.status = status;
        this.code = code;
    }
}

function getCookie(name: string): string | undefined {
    const prefix = `${name}=`;
    const cookie = document.cookie.split('; ').find((item) => item.startsWith(prefix));
    return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : undefined;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const csrfToken = getCookie('csrftoken');
    const isFormData = options.body instanceof FormData;
    const response = await fetch(path, {
        credentials: 'same-origin',
        ...options,
        headers: {
            Accept: 'application/vnd.cvat+json',
            ...(options.body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
            ...(csrfToken ? { 'X-CSRFTOKEN': csrfToken } : {}),
            ...options.headers,
        },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new LocalAPIError(
            response.status,
            body.message || body.detail || '请求失败，请稍后重试。',
            body.code,
        );
    }
    return body as T;
}

export function listWorkspace(path: string): Promise<WorkspaceEntry[]> {
    const query = new URLSearchParams();
    if (path) query.set('path', path);
    return request<WorkspaceEntry[]>(`/api/local/workspace?${query.toString()}`);
}

export function listVideos(): Promise<VideoMetadata[]> {
    return request<VideoMetadata[]>('/api/local/videos');
}

export function createExtraction(parameters: ExtractionParameters): Promise<{ id: string; status: string }> {
    return request('/api/local/extractions', {
        method: 'POST',
        body: JSON.stringify(parameters),
    });
}

export function getExtraction(id: string): Promise<ExtractionStatus> {
    return request<ExtractionStatus>(`/api/local/extractions/${encodeURIComponent(id)}`);
}

export function listAppendableTasks(): Promise<AppendableTask[]> {
    return request<AppendableTask[]>('/api/local/tasks');
}

export function appendTaskImages(taskID: number, path: string): Promise<TaskImageAppendResult> {
    return request<TaskImageAppendResult>(`/api/local/tasks/${taskID}/images`, {
        method: 'POST',
        body: JSON.stringify({ path }),
    });
}

export function createPackageImport(name: string, file: File): Promise<{ id: string; status: string }> {
    const form = new FormData();
    form.append('name', name);
    form.append('file', file);
    return request('/api/local/packages', { method: 'POST', body: form });
}

export function getPackageImport(id: string): Promise<PackageImportStatus> {
    return request<PackageImportStatus>(`/api/local/packages/${encodeURIComponent(id)}`);
}

export function getFrameStatus(taskID: number, frame: number): Promise<FrameStatus> {
    return request<FrameStatus>(`/api/local/tasks/${taskID}/frames/${frame}/status`);
}

export async function completeFrame(taskID: number, frame: number): Promise<FrameStatus> {
    const result = await request<FrameStatus>(`/api/local/tasks/${taskID}/frames/${frame}/status`, {
        method: 'POST',
    });
    window.dispatchEvent(new CustomEvent(FRAME_STATUS_UPDATED_EVENT, {
        detail: { taskID, frame, status: result.status },
    }));
    return result;
}

export function getTaskReview(taskID: number): Promise<TaskReviewSummary> {
    return request<TaskReviewSummary>(`/api/local/tasks/${taskID}/review`);
}

export function completeTaskReview(taskID: number): Promise<TaskReviewSummary> {
    return request<TaskReviewSummary>(`/api/local/tasks/${taskID}/review`, { method: 'POST' });
}
