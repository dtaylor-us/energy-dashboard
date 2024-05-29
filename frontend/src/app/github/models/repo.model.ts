// src/app/github/models/repo.model.ts

export interface Repo {
  id: number;
  name: string;
  description: string;
  html_url: string; // The URL to the repo on GitHub.
}
