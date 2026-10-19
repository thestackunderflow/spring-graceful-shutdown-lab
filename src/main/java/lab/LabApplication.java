package lab;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class LabApplication {

    private static final Logger log = LoggerFactory.getLogger(LabApplication.class);

    public static void main(String[] args) {
        SpringApplication.run(LabApplication.class, args);
    }

    @GetMapping("/hello")
    String hello() {
        return "Hello";
    }

    /** A request that takes N seconds: the "live request" that is still running when the container is stopped. */
    @GetMapping("/slow")
    String slow(@RequestParam(defaultValue = "20") int seconds) throws InterruptedException {
        log.info("slow request started ({} s)", seconds);
        Thread.sleep(seconds * 1000L);
        log.info("slow request finished ({} s)", seconds);
        return "done after " + seconds + " s";
    }
}
