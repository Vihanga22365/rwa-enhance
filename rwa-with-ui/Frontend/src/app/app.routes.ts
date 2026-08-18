import { Routes } from '@angular/router';

import { DashboardComponent } from './dashboard/dashboard.component';
import { MainComponent } from './main/main.component';
import { RwaAgentComponent } from './rwa-agent/rwa-agent.component';

export const routes: Routes = [
  {
    path: '',
    component: MainComponent,
    children: [
      { path: '', component: DashboardComponent },
      { path: 'rwa-agent', component: RwaAgentComponent },
    ],
  },
  { path: '**', redirectTo: '' },
];
