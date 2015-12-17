//Check if a website is down or not.
package down

import (
        "net/http"
        "strings"
        "time"
)

func down(msg Message) []string {

        //only checking http so we don't have to explicitly check for https
        pre := "http"
        var url string

        if !strings.HasPrefix(msg.line, pre) {
                url = pre + "://"
        }

        timeout := time.Duration(7 * time.Second)
        client := http.Client{Timeout: timeout}

        url += msg.line

        _, err := client.Get(url)

        if err == nil {
                return []string{"It's just you, " + url + " is up."}
        } else {
                return []string{"It's not just you, " + url + " seems to be down."}
        }
}