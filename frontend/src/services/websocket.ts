import { ProcessingLog, PipelineStage } from '../types';

type MessageCallback = (data: {
  type: 'log' | 'progress' | 'stage_change' | 'clip_ready' | 'error';
  project_id?: string;
  stage?: PipelineStage;
  progress?: number;
  log?: ProcessingLog;
  clip_id?: string;
  message?: string;
}) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Set<MessageCallback> = new Set();
  private reconnectTimeout: any = null;
  private isConnecting: boolean = false;

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isConnecting = true;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/logs`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnecting = false;
        console.log('[ClipForge WS] Connected to live pipeline stream');
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.listeners.forEach((callback) => callback(payload));
        } catch (e) {
          console.error('[ClipForge WS] Parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.warn('[ClipForge WS] WebSocket error:', err);
        this.ws?.close();
      };
    } catch (e) {
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) return;
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, 3000);
  }

  public subscribe(callback: MessageCallback): () => void {
    this.listeners.add(callback);
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.connect();
    }
    return () => {
      this.listeners.delete(callback);
    };
  }
}

export const wsClient = new WebSocketClient();
