import { CommonModule } from '@angular/common';
import {
  AfterViewChecked,
  Component,
  ElementRef,
  ViewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiMessage, RwaAgentApiService } from './rwa-agent-api.service';

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  at: Date;
  label?: string;
  isExpanded?: boolean;
};

@Component({
  selector: 'app-rwa-agent',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './rwa-agent.component.html',
  styleUrl: './rwa-agent.component.scss',
})
export class RwaAgentComponent implements AfterViewChecked {
  private readonly storageKey = 'rwa-agent-chat-history-v1';
  private readonly legacyGreeting =
    'Hi — paste an email subject + content on the left, then click Submit. You can also chat here.';
  private shouldScrollToBottom = false;

  @ViewChild('chatScrollContainer')
  private readonly chatScrollContainer?: ElementRef<HTMLDivElement>;

  emailText = '';
  chatInput = '';
  issueType = '';
  sessionId = '';
  submittedEmailText = '';
  isSubmittingEmail = false;
  isSendingFollowUp = false;

  messages: ChatMessage[] = [];

  constructor(private readonly rwaAgentApi: RwaAgentApiService) {
    this.clearPersistedState();
    this.queueScrollToBottom();
  }

  ngAfterViewChecked(): void {
    if (!this.shouldScrollToBottom) {
      return;
    }

    this.scrollToBottom();
    this.shouldScrollToBottom = false;
  }

  submitEmail(): void {
    const trimmed = this.emailText.trim();
    if (!trimmed || this.isSubmittingEmail || this.isSendingFollowUp) return;

    this.isSubmittingEmail = true;
    this.queueScrollToBottom();
    this.rwaAgentApi
      .submitEmail({
        input_text: trimmed,
        session_id: this.sessionId || undefined,
      })
      .pipe(
        finalize(() => {
          this.isSubmittingEmail = false;
        }),
      )
      .subscribe({
        next: (response) => {
          this.issueType = response.issue_type;
          this.sessionId = response.session_id;
          this.submittedEmailText = trimmed;
          this.messages = [
            ...this.messages,
            ...this.toChatMessages(response.messages),
          ];
          this.queueScrollToBottom();
        },
        error: () => {
          this.messages = [
            ...this.messages,
            {
              role: 'assistant',
              content:
                'Unable to process the email right now. Please check backend service and try again.',
              at: new Date(),
            },
          ];
          this.queueScrollToBottom();
        },
      });
  }

  sendChat(): void {
    const trimmed = this.chatInput.trim();
    if (!trimmed || this.isSubmittingEmail || this.isSendingFollowUp) return;

    const inputText = this.submittedEmailText || this.emailText.trim();

    this.closeAllExpanders();

    this.messages = [
      ...this.messages,
      { role: 'user', content: trimmed, at: new Date() },
    ];
    this.chatInput = '';
    this.isSendingFollowUp = true;
    this.queueScrollToBottom();

    this.rwaAgentApi
      .sendFollowUp({
        input_text: inputText,
        user_chat_input: trimmed,
        issue_type: this.issueType || undefined,
        session_id: this.sessionId || undefined,
      })
      .pipe(
        finalize(() => {
          this.isSendingFollowUp = false;
        }),
      )
      .subscribe({
        next: (response) => {
          this.issueType = response.issue_type;
          this.sessionId = response.session_id;
          this.messages = [
            ...this.messages,
            ...this.toChatMessages(response.messages),
          ];
          this.queueScrollToBottom();
        },
        error: () => {
          this.messages = [
            ...this.messages,
            {
              role: 'assistant',
              content:
                'Unable to process the follow-up right now. Please check backend service and try again.',
              at: new Date(),
            },
          ];
          this.queueScrollToBottom();
        },
      });
  }

  toggleExpander(message: ChatMessage): void {
    message.isExpanded = !message.isExpanded;
  }

  onEmailInputChanged(): void {}

  onChatInputChanged(): void {}

  refreshWorkspace(): void {
    this.emailText = '';
    this.chatInput = '';
    this.issueType = '';
    this.sessionId = '';
    this.submittedEmailText = '';
    this.isSubmittingEmail = false;
    this.isSendingFollowUp = false;
    this.messages = [];

    this.clearPersistedState();
    this.queueScrollToBottom();
  }

  private toChatMessages(messages: ApiMessage[]): ChatMessage[] {
    return messages.map((message) => ({
      role: message.role,
      content: message.content,
      label: message.label,
      isExpanded: false,
      at: new Date(),
    }));
  }

  private clearPersistedState(): void {
    localStorage.removeItem(this.storageKey);
  }

  private queueScrollToBottom(): void {
    this.shouldScrollToBottom = true;
  }

  private scrollToBottom(): void {
    const container = this.chatScrollContainer?.nativeElement;
    if (!container) {
      return;
    }

    container.scrollTop = container.scrollHeight;
  }

  private closeAllExpanders(): void {
    for (const message of this.messages) {
      if (message.label && message.isExpanded) {
        message.isExpanded = false;
      }
    }
  }

  trackByIndex = (i: number) => i;
}
