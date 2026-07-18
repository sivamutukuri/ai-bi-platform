import { getToken } from "./api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || "/api/v1";

export interface StreamMetrics {
  stream_id: string;
  record_count: number;
  batch_count: number;
  records_per_second: number;
  started_at: number;
  last_event_at: number;
  averages: Record<string, number>;
  minimums: Record<string, number>;
  maximums: Record<string, number>;
  null_counts: Record<string, number>;
}

export interface StreamEvent {
  type: string;
  data?: StreamMetrics;
  detail?: string;
}

/**
 * Subscribe to live stream metrics using Server-Sent Events.
 * EventSource cannot set headers, so the JWT is passed as a query param.
 * Returns a cleanup function that closes the connection.
 */
export function subscribeToStream(
  streamId: string,
  onMetrics: (metrics: StreamMetrics) => void,
  onError?: (err: Event) => void
): () => void {
  const token = getToken();
  const url =
    `${API_URL}${API_PREFIX}/streaming/${encodeURIComponent(streamId)}/events` +
    (token ? `?token=${encodeURIComponent(token)}` : "");
  const source = new EventSource(url);

  source.onmessage = (event: MessageEvent) => {
    try {
      const parsed: StreamEvent = JSON.parse(event.data);
      if (parsed.type === "metrics" && parsed.data) {
        onMetrics(parsed.data);
      }
    } catch {
      /* ignore keep-alive / malformed frames */
    }
  };

  source.onerror = (err) => {
    onError?.(err);
  };

  return () => source.close();
}

/**
 * Open a WebSocket for pushing record batches to a stream.
 */
export function openStreamSocket(streamId: string): WebSocket {
  const wsBase = API_URL.replace(/^http/, "ws");
  const socket = new WebSocket(
    `${wsBase}${API_PREFIX}/streaming/${encodeURIComponent(streamId)}/ws`
  );
  return socket;
}

/**
 * Push a batch of records over HTTP (fallback / simple producers).
 */
export async function ingestBatch(
  streamId: string,
  records: Record<string, unknown>[]
): Promise<void> {
  const token = getToken();
  await fetch(
    `${API_URL}${API_PREFIX}/streaming/${encodeURIComponent(streamId)}/ingest`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ stream_id: streamId, records }),
    }
  );
}
