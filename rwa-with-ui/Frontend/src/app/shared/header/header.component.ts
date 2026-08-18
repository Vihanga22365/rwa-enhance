import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { APP_CONSTANTS } from '../../constants';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
})
export class HeaderComponent {
  readonly constants = APP_CONSTANTS;

  user = {
    greeting: 'Welcome back,',
    name: 'Sarah Chen',
    desk: 'Fixed Income Desk',
  };
}
