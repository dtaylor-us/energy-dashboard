package us.dtaylor.gh

import io.quarkus.test.junit.QuarkusTest
import io.restassured.RestAssured.given
import org.hamcrest.CoreMatchers.notNullValue
import org.junit.jupiter.api.Test

@QuarkusTest
class GithubServiceIT {

    @Test
    fun testGithubEndpoint() {
        val username = "testUser"

        given()
                .pathParam("username", username)
                .`when`().get("/api/v1/github/repos/{username}")
                .then()
                .statusCode(200)
                .body("$", notNullValue())  // assumes endpoint returns a list; adjust accordingly
    }
}
