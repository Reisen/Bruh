//Choose randomly from a set of choices separated by commas.
package choose

import (
        "math/rand"
        "strings"
)

func Choose(msg Message) []string {

        tmp := strings.Split(msg.line, ",")

        var choice int

        if len(tmp) <= 1 {
                choice = 0
        } else {
                choice = rand.Intn(len(tmp) - 1)
        }

        return []string{tmp[choice]}
}