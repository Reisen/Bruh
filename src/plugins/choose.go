//Choose randomly from a set of choices separated by commas.
package plugins

import (
	"math/rand"
	"strings"
	"walnut"
)

func Choose(c walnut.Command) string {
	msg := c.Message
	tmp := strings.Split(msg.Line, ",")

	var choice int

	if len(tmp) <= 1 {
		choice = 0
	} else {
		choice = rand.Intn(len(tmp) - 1)
	}

	return tmp[choice]
}
