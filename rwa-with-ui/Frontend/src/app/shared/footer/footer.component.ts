import { Component } from '@angular/core';
import { APP_CONSTANTS } from '../../constants';

@Component({
  selector: 'app-footer',
  standalone: true,
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.scss',
})
export class FooterComponent {
  readonly constants = APP_CONSTANTS;
}
