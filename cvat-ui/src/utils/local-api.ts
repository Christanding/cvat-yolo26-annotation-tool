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
    const response = await fetch(path, {
        credentials: 'same-origin',
        ...options,
        headers: {
            Accept: 'application/vnd.cvat+json',
            ...(options.body ? { 'Content-Type': 'application/json' } : {}),
            ...(csrfToken ? { 'X-CSRFTOKEN': csrfToken } : {}),
            ...options.headers,
        },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new LocalAPIError(
            response.status,
            body.message || '请求失败，请稍后重试。',
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
