package us.dtaylor.gh.v1

import jakarta.inject.Inject
import jakarta.ws.rs.GET
import jakarta.ws.rs.Path
import jakarta.ws.rs.PathParam
import jakarta.ws.rs.Produces
import jakarta.ws.rs.core.MediaType

@Path("/api/v1/github")
class GithubResource {

    @Inject
    lateinit var githubService: GithubService

    @GET
    @Path("/repos/{username}")
    @Produces(MediaType.APPLICATION_JSON)
    fun listRepos(@PathParam("username") username: String): List<Repo> {
        return githubService.listUserRepos(username)
    }
}
