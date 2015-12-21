package urban

import (
	"net/http"
	"io/ioutil"
	"encoding/json"
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


func Urban(msg Message) []string {

	res, _ := http.Get("http://api.urbandictionary.com/v0/define?term=" + msg.line)
	defer res.Body.Close()


	content, _ := ioutil.ReadAll(res.Body)


	var parse  document
	json.Unmarshal(content, &parse)
	
	return []string{msg.line + " - " + parse.List[0].Definition}
}