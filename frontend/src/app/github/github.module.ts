import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {RepoListComponent} from './repo-list/repo-list.component';
import {RepoDetailComponent} from './repo-detail/repo-detail.component';
import {HttpClientModule} from '@angular/common/http';
import {GithubService} from "./github.service";
import {FormsModule} from "@angular/forms";
import {GithubRoutingModule} from "./github-routing.module";
import { SidebarModule } from 'primeng/sidebar';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';

@NgModule({
  declarations: [
    RepoListComponent,
    RepoDetailComponent
  ],
  exports: [RepoListComponent],
  providers: [GithubService],
  imports: [
    CommonModule,
    HttpClientModule,
    FormsModule,
    InputTextModule,
    ButtonModule,
    GithubRoutingModule,
  ]
})
export class GithubModule { }
