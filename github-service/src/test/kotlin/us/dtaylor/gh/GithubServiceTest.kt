package us.dtaylor.gh

import io.quarkus.test.InjectMock
import io.quarkus.test.junit.QuarkusTest
import jakarta.inject.Inject
import org.eclipse.microprofile.rest.client.inject.RestClient
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import org.mockito.Mockito.verify
import org.mockito.Mockito.`when`
import us.dtaylor.gh.v1.GithubApi
import us.dtaylor.gh.v1.GithubService
import us.dtaylor.gh.v1.Repo

@QuarkusTest
class GithubServiceTest {

    @Inject
    lateinit var githubService: GithubService

    @InjectMock
    @RestClient
    lateinit var githubApi: GithubApi

    @Test
    fun testListUserRepos() {
        val mockRepoList = listOf(Repo(id = 1L, html_url = "http://google.com", name = "google"))  // populate with mock data
        val username = "testUser"

        `when`(githubApi.listRepos(username)).thenReturn(mockRepoList)

        val result = githubService.listUserRepos(username)

        verify(githubApi).listRepos(username)
        assertEquals(mockRepoList, result)
    }
}
