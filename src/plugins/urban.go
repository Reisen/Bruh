package plugins

import (
	"net/http"
	"io/ioutil"
	"encoding/json"
    "walnut"
)

type document struct {

	Tags []string
	Result_type string
	List []def
}

type def struct {

	Defid int
	Word string
	Author string
	Permalink string
	Definition string
	Example string
	ThumpsUp string
	ThumbsDown string
	CurrentVote string
}


func Urban(c walnut.Command) string {
    msg := c.Message
	res, _ := http.Get("http://api.urbandictionary.com/v0/define?term=" + msg.Line)
	defer res.Body.Close()


	content, _ := ioutil.ReadAll(res.Body)


	var parse  document
	json.Unmarshal(content, &parse)

	return msg.Line + " - " + parse.List[0].Definition
}
