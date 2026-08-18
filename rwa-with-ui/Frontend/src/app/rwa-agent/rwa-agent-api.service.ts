import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type ApiMessage = {
  role: 'user' | 'assistant';
  content: string;
  label?: string;
};

export type EmailSubmitRequest = {
  input_text: string;
  session_id?: string;
};

export type EmailSubmitResponse = {
  session_id: string;
  issue_type: string;
  messages: ApiMessage[];
};

export type FollowUpRequest = {
  input_text: string;
  user_chat_input: string;
  issue_type?: string;
  session_id?: string;
};

export type FollowUpResponse = {
  session_id: string;
  issue_type: string;
  messages: ApiMessage[];
};

/**
 * Where the API lives, relative to wherever this bundle is served from.
 *
 * In production the SPA sits under a sub-path (/rwa-enhance/) because the
 * server's port 80 hosts several apps side by side, and nginx forwards
 * /rwa-enhance/api/... to the backend after stripping the prefix. Resolving
 * against `document.baseURI` — which is the <base href> Angular compiled in —
 * keeps that prefix in exactly one place (the build's --base-href) instead of
 * duplicating it here.
 *
 * In development `apiBaseUrl` is an absolute origin (http://host:8000), so the
 * base href plays no part and the URL is used as-is.
 */
function resolveApiBaseUrl(): string {
  if (environment.apiBaseUrl) {
    return `${environment.apiBaseUrl}/api/rwa`;
  }
  const { pathname, search } = new URL('api/rwa', document.baseURI);
  return `${pathname}${search}`;
}

@Injectable({ providedIn: 'root' })
export class RwaAgentApiService {
  private readonly baseUrl = resolveApiBaseUrl();

  constructor(private readonly http: HttpClient) {}

  submitEmail(payload: EmailSubmitRequest): Observable<EmailSubmitResponse> {
    return this.http.post<EmailSubmitResponse>(
      `${this.baseUrl}/email-submit`,
      payload,
    );
  }

  sendFollowUp(payload: FollowUpRequest): Observable<FollowUpResponse> {
    return this.http.post<FollowUpResponse>(
      `${this.baseUrl}/follow-up`,
      payload,
    );
  }
}
