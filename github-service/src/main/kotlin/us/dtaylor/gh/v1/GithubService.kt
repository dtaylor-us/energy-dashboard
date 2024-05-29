package us.dtaylor.gh.v1


import jakarta.enterprise.context.ApplicationScoped
import jakarta.inject.Inject
import org.eclipse.microprofile.rest.client.inject.RestClient


@ApplicationScoped
class GithubService {

    @Inject
    @RestClient
    lateinit var githubApi: GithubApi

    fun listUserRepos(username: String): List<Repo> {
        return githubApi.listRepos(username)
    }
}
