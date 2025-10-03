export type ApiSuccess<T> = {
  success: true;
  data: T;
  message?: string;
  trace_id: string;
};

export type ApiErrorPayload = {
  success: false;
  message?: string;
  trace_id: string;
  error: {
    type: string;
    context?: Record<string, unknown>;
    i18n_key?: string;
    i18n_params?: Record<string, string | number>;
  };
  retry_info?: {
    retryable: boolean;
    retry_after_ms?: number;
  };
};

export type ApiResponse<T> = ApiSuccess<T> | ApiErrorPayload;

export type Envelope<T> = ApiResponse<T>;
