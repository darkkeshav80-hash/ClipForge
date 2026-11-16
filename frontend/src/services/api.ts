import { 
  Project, 
  Clip, 
  CaptionStyleConfig, 
  AIProvider, 
  TaskModelAssignment, 
  AutomationSettings, 
  HardwareProfileConfig,
  YouTubeStudioStatus,
  DashboardMetrics 
} from '../types';

const API_BASE = '/api';

export const api = {
  // Metrics & Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const res = await fetch(`${API_BASE}/analytics/metrics`);
    if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
    return res.json();
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async getProject(id: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch project ${id}`);
    return res.json();
  },

  async createProject(data: Partial<Project>): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create project');
    return res.json();
  },

  async deleteProject(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to delete project ${id}`);
  },

  // Video Upload & URL Import
  async uploadVideo(file: File, onProgress?: (percent: number) => void): Promise<{ path: string; filename: string; duration: number; width: number; height: number; fps: number; thumbnail_path: string }> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE}/videos/upload`);
      
      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (e) {
            reject(new Error('Invalid JSON response from server'));
          }
        } else {
          reject(new Error(xhr.responseText || 'Upload failed'));
        }
      };

      xhr.onerror = () => reject(new Error('Network error during upload'));

      const formData = new FormData();
      formData.append('file', file);
      xhr.send(formData);
    });
  },

  async importVideoUrl(url: string): Promise<{ title: string; duration: number; thumbnail_url: string; video_path: string; metadata: any }> {
    const res = await fetch(`${API_BASE}/videos/import-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to inspect URL' }));
      throw new Error(err.detail || 'Failed to inspect URL');
    }
    return res.json();
  },

  // Clips
  async getClips(projectId?: string): Promise<Clip[]> {
    const url = projectId ? `${API_BASE}/clips?project_id=${projectId}` : `${API_BASE}/clips`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch clips');
    return res.json();
  },

  async getClip(id: string): Promise<Clip> {
    const res = await fetch(`${API_BASE}/clips/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch clip ${id}`);
    return res.json();
  },

  async deleteClip(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/clips/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to delete clip ${id}`);
  },

  async updateClip(id: string, updates: Partial<Clip>): Promise<Clip> {
    const res = await fetch(`${API_BASE}/clips/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!res.ok) throw new Error(`Failed to update clip ${id}`);
    return res.json();
  },

  async renderClip(id: string, options?: any): Promise<{ job_id?: string; message: string; warning?: string; rendered_path?: string; language?: string }> {
    const res = await fetch(`${API_BASE}/clips/${id}/render`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options || {}),
    });
    if (!res.ok) throw new Error('Failed to render clip');
    return res.json();
  },

  async applyCaptionsToProject(projectId: string, options: any): Promise<{ success: boolean; message: string; updated_count: number }> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/apply-captions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options || {}),
    });
    if (!res.ok) throw new Error('Failed to apply captions to project');
    return res.json();
  },

  // Caption Presets
  async getCaptionPresets(): Promise<CaptionStyleConfig[]> {
    const res = await fetch(`${API_BASE}/captions/presets`);
    if (!res.ok) throw new Error('Failed to fetch caption presets');
    return res.json();
  },

  async saveCaptionPreset(preset: CaptionStyleConfig): Promise<CaptionStyleConfig> {
    const res = await fetch(`${API_BASE}/captions/presets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preset),
    });
    if (!res.ok) throw new Error('Failed to save caption preset');
    return res.json();
  },

  async getCaptionPreview(payload: any): Promise<{ success: boolean; preview_url: string; original_url?: string; duration: number; cached: boolean }> {
    const res = await fetch(`${API_BASE}/captions/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) throw new Error('Failed to generate caption preview');
    return res.json();
  },

  // AI Providers & Models
  async getProviders(): Promise<AIProvider[]> {
    const res = await fetch(`${API_BASE}/providers`);
    if (!res.ok) throw new Error('Failed to fetch AI providers');
    return res.json();
  },

  async updateProvider(provider: AIProvider): Promise<AIProvider> {
    const res = await fetch(`${API_BASE}/providers/${provider.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(provider),
    });
    if (!res.ok) throw new Error(`Failed to update provider ${provider.id}`);
    return res.json();
  },

  async testProvider(providerId: string): Promise<{ success: boolean; models: string[]; message: string }> {
    const res = await fetch(`${API_BASE}/providers/${providerId}/test`, { method: 'POST' });
    if (!res.ok) throw new Error('Provider test failed');
    return res.json();
  },

  async getTaskAssignments(): Promise<TaskModelAssignment[]> {
    const res = await fetch(`${API_BASE}/models/assignments`);
    if (!res.ok) throw new Error('Failed to fetch model assignments');
    return res.json();
  },

  async saveTaskAssignments(assignments: TaskModelAssignment[]): Promise<void> {
    const res = await fetch(`${API_BASE}/models/assignments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(assignments),
    });
    if (!res.ok) throw new Error('Failed to save model assignments');
  },

  // Automation & Queue
  async getAutomationSettings(): Promise<AutomationSettings> {
    const res = await fetch(`${API_BASE}/automation/settings`);
    if (!res.ok) throw new Error('Failed to fetch automation settings');
    return res.json();
  },

  async saveAutomationSettings(settings: AutomationSettings): Promise<AutomationSettings> {
    const res = await fetch(`${API_BASE}/automation/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error('Failed to save automation settings');
    return res.json();
  },

  async controlAutomation(action: 'start' | 'pause' | 'resume' | 'stop', projectId?: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/automation/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, project_id: projectId }),
    });
    if (!res.ok) throw new Error(`Failed to ${action} automation`);
    return res.json();
  },

  // YouTube Studio
  async getYouTubeStatus(): Promise<YouTubeStudioStatus> {
    const res = await fetch(`${API_BASE}/youtube/status`);
    if (!res.ok) throw new Error('Failed to fetch YouTube status');
    return res.json();
  },

  async publishToYouTube(clipId: string, metadata: { title: string; description: string; tags: string[]; privacy: 'public' | 'unlisted' | 'private'; schedule_time?: string }): Promise<{ success: boolean; video_id?: string; url?: string; message: string }> {
    const res = await fetch(`${API_BASE}/youtube/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_id: clipId, ...metadata }),
    });
    if (!res.ok) throw new Error('Failed to publish to YouTube');
    return res.json();
  },

  // System & Hardware
  async getSystemSettings(): Promise<{ hardware: HardwareProfileConfig; detected_hardware: any; storage: any; low_performance_mode: boolean }> {
    const res = await fetch(`${API_BASE}/system/settings`);
    if (!res.ok) throw new Error('Failed to fetch system settings');
    return res.json();
  },

  async updateSystemSettings(settings: any): Promise<void> {
    const res = await fetch(`${API_BASE}/system/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error('Failed to update system settings');
  },

  async triggerStorageCleanup(daysOld: number = 7): Promise<{ freed_mb: number; message: string }> {
    const res = await fetch(`${API_BASE}/system/cleanup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ days_old: daysOld }),
    });
    if (!res.ok) throw new Error('Storage cleanup failed');
    return res.json();
  }
};
