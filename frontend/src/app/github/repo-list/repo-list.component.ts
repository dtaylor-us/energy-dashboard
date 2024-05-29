import { Component, OnInit } from '@angular/core';
import {GithubService} from "../github.service";
import {Repo} from "../models/repo.model";

@Component({
  selector: 'app-repo-list',
  templateUrl: './repo-list.component.html',
  styleUrls: ['./repo-list.component.scss']
})
export class RepoListComponent implements OnInit {

  username: string = '';
  repos: Repo[] = [];

  constructor(private githubRepoService: GithubService) { }

  ngOnInit(): void { }

  fetchRepos() {
    if (this.username) {
      this.githubRepoService.listRepos(this.username).subscribe(data => {
        this.repos = data;
      });
    }
  }
}
