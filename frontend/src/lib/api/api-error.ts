import type { ApiErrorPayload } from "./types";

export class ApiError extends Error {
  public readonly type: string;

  public readonly status: number;

  public readonly traceId?: string;

  public readonly i18nKey?: string;

  public readonly i18nParams?: Record<string, string | number>;

  public readonly retryInfo?: ApiErrorPayload["retry_info"];

  constructor(
    status: number,
    type: string,
    traceId: string | undefined,
    message: string | undefined,
    i18nKey?: string,
    i18nParams?: Record<string, string | number>,
    retryInfo?: ApiErrorPayload["retry_info"],
  ) {
    super(message ?? type);
    this.name = "ApiError";
    this.status = status;
    this.type = type;
    this.traceId = traceId;
    this.i18nKey = i18nKey;
    this.i18nParams = i18nParams;
    this.retryInfo = retryInfo;
  }

  static fromPayload(status: number, payload: ApiErrorPayload) {
    const { error, message, retry_info, trace_id } = payload;
    return new ApiError(
      status,
      error?.type ?? "UnknownError",
      trace_id,
      message ?? error?.type,
      error?.i18n_key,
      error?.i18n_params,
      retry_info,
    );
  }

  tooManyRequests() {
    return this.status === 429;
  }

  isRetryable() {
    return Boolean(this.retryInfo?.retryable);
  }
}
