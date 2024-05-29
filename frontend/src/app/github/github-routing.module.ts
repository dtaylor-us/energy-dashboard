import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {RepoListComponent} from "./repo-list/repo-list.component";
import {RepoDetailComponent} from "./repo-detail/repo-detail.component";

const routes: Routes = [
  { path: '', component: RepoListComponent },
  { path: ':id', component: RepoDetailComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class GithubRoutingModule { }
