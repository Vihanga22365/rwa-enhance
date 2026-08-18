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

@Injectable({ providedIn: 'root' })
export class RwaAgentApiService {
  private readonly baseUrl = `${environment.apiBaseUrl}/api/rwa`;

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
