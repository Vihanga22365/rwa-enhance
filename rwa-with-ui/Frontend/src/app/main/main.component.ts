import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { HeaderComponent } from '../shared/header/header.component';
import {
  NavigationEnd,
  Router,
  RouterLink,
  RouterOutlet,
} from '@angular/router';
import { filter } from 'rxjs';

@Component({
  selector: 'app-main',
  standalone: true,
  imports: [CommonModule, HeaderComponent, RouterOutlet, RouterLink],
  templateUrl: './main.component.html',
  styleUrl: './main.component.scss',
})
export class MainComponent {
  showFab = true;
  isRwaRoute = false;

  constructor(private readonly router: Router) {
    this.updateRouteUiState(this.router.url);

    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe((e) => {
        this.updateRouteUiState(e.urlAfterRedirects);
      });
  }

  private updateRouteUiState(url: string): void {
    this.isRwaRoute = url === '/rwa-agent';
    this.showFab = !this.isRwaRoute;
  }
}
