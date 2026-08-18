import { Component } from '@angular/core';
import { APP_CONSTANTS } from '../constants';

type TrendDirection = 'up' | 'down';
type SummaryIndicator = 'trend' | 'none' | 'alert';

type SummaryCard = {
  title: string;
  badge: string;
  value: string;
  footnote: string;
  indicator: SummaryIndicator;
  indicatorDirection?: TrendDirection;
  accentBorderClass: string;
  badgeClass: string;
  trendClass: string;
};

type RwaChangeRow = {
  tradeId: string;
  product: string;
  counterparty: string;
  date: string;
  before: string;
  after: string;
  delta: string;
  deltaPct: string;
  direction: TrendDirection;
};

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  readonly constants = APP_CONSTANTS;

  summaryCards: SummaryCard[] = [
    {
      title: 'Total RWA',
      badge: 'Portfolio',
      value: '$284.5M',
      footnote: '2.3% vs last week',
      indicator: 'trend',
      indicatorDirection: 'down',
      accentBorderClass: 'border-[#2A64FF]',
      badgeClass: 'bg-[#EAF1FF] text-[#2A64FF]',
      trendClass: 'text-emerald-600',
    },
    {
      title: 'Capital Requirement',
      badge: 'Basel III',
      value: '$22.76M',
      footnote: '8% capital ratio',
      indicator: 'none',
      accentBorderClass: 'border-[#F6A21A]',
      badgeClass: 'bg-[#FFF3DE] text-[#C77700]',
      trendClass: 'text-slate-500',
    },
    {
      title: 'Changes Last 48h',
      badge: 'Alert',
      value: '12 trades',
      footnote: '4 require review',
      indicator: 'alert',
      indicatorDirection: 'up',
      accentBorderClass: 'border-[#FF5C7A]',
      badgeClass: 'bg-[#FFE7ED] text-[#D81B44]',
      trendClass: 'text-rose-600',
    },
  ];

  rows: RwaChangeRow[] = [
    {
      tradeId: 'TRD-2026-00147',
      product: 'Interest Rate Swap',
      counterparty: 'Goldman Sachs',
      date: '2026-01-15',
      before: '$4,850,000',
      after: '$5,920,000',
      delta: '+ $1,070,000',
      deltaPct: '+22.1%',
      direction: 'up',
    },
    {
      tradeId: 'TRD-2026-00132',
      product: 'Credit Default Swap',
      counterparty: 'JP Morgan',
      date: '2026-01-14',
      before: '$8,200,000',
      after: '$7,450,000',
      delta: '- $750,000',
      deltaPct: '-9.1%',
      direction: 'down',
    },
    {
      tradeId: 'TRD-2026-00156',
      product: 'FX Forward',
      counterparty: 'Morgan Stanley',
      date: '2026-01-15',
      before: '$2,100,000',
      after: '$2,890,000',
      delta: '+ $790,000',
      deltaPct: '+37.6%',
      direction: 'up',
    },
    {
      tradeId: 'TRD-2026-00098',
      product: 'Equity Option',
      counterparty: 'Bank of America',
      date: '2026-01-13',
      before: '$3,500,000',
      after: '$3,150,000',
      delta: '- $350,000',
      deltaPct: '-10%',
      direction: 'down',
    },
  ];

  getDeltaClasses(direction: TrendDirection) {
    return direction === 'up' ? 'text-rose-600' : 'text-emerald-600';
  }
}
