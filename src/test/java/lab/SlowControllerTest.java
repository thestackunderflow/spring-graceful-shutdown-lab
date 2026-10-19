package lab;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class SlowControllerTest {

    @LocalServerPort
    int port;

    String get(String path) throws Exception {
        HttpResponse<String> r = HttpClient.newHttpClient().send(
                HttpRequest.newBuilder(URI.create("http://localhost:" + port + path)).build(),
                HttpResponse.BodyHandlers.ofString());
        return r.body();
    }

    @Test
    void helloAnswersAtOnce() throws Exception {
        assertThat(get("/hello")).isEqualTo("Hello");
    }

    @Test
    void slowAnswersAfterTheGivenSeconds() throws Exception {
        long t = System.nanoTime();
        assertThat(get("/slow?seconds=1")).isEqualTo("done after 1 s");
        assertThat((System.nanoTime() - t) / 1_000_000).isGreaterThanOrEqualTo(1000);
    }
}
