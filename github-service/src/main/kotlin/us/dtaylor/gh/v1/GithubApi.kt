package us.dtaylor.gh.v1

import jakarta.enterprise.context.ApplicationScoped
import jakarta.ws.rs.GET
import jakarta.ws.rs.Path
import jakarta.ws.rs.PathParam
import org.eclipse.microprofile.rest.client.inject.RegisterRestClient

@Path("/users")
@RegisterRestClient(baseUri = "https://api.github.com")
@ApplicationScoped
fun interface GithubApi {
    @GET
    @Path("/{username}/repos")
    fun listRepos(@PathParam("username") username: String) :List<Repo>
}

data class Repo(val id: Long, val name: String, val html_url: String)
