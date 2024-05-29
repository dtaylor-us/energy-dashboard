import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {Repo} from "./models/repo.model";

@Injectable({
  providedIn: 'root'
})
export class GithubService {
  private readonly API_HOST = environment.apiHost;

  constructor(private http: HttpClient) {}

  listRepos(username: string): Observable<Repo[]> {
    return this.http.get<Repo[]>(`${this.API_HOST}/api/v1/github/repos/${username}`)
  }
}
