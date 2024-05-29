import {Component, ViewChild} from '@angular/core';
import {MenuItem} from "primeng/api";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  @ViewChild('menu') menu: any;

  menuItems: MenuItem[] = [
    {
      label: 'Github Repos',
      icon: 'pi pi-code',
      routerLink: '/github'
    }
    // ... add more items as needed
  ];

  title = 'frontend';

  toggleMenu(event: any) {
    if (this.menu) {
      this.menu.toggle(event);
    }
  }
}
