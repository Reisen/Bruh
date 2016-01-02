//Check if a website is down or not.
package plugins

import (
        "net/http"
        "strings"
        "time"
        "walnut"
)

func Down(c walnut.Command) string {
        msg := c.Message

        //only checking http so we don't have to explicitly check for https
        pre := "http"
        var url string

        if !strings.HasPrefix(msg.Line, pre) {
                url = pre + "://"
        }

        timeout := time.Duration(7 * time.Second)
        client := http.Client{Timeout: timeout}

        url += msg.Line

        _, err := client.Get(url)

        if err == nil {
                return "It's just you, " + url + " is up."
        } else {
                return "It's not just you, " + url + " seems to be down."
        }
}
