package walnut

import (
	"github.com/gdamore/mangos"
	"github.com/gdamore/mangos/protocol/push"
	"github.com/gdamore/mangos/protocol/sub"
	"github.com/gdamore/mangos/transport/tcp"
	"gopkg.in/vmihailenco/msgpack.v2"
	"strings"
)

type Message struct {
	Protocol string
	From     string
	To       string
	Line     string
	Meta     string
}

type Command struct {
	Command string
	Text    string
	Message Message
}

type Context struct {
	messages []func(Message) string
	commands map[string]func(Command) string
}

func MakeContext() Context {
	return Context{
		messages: make([]func(Message) string, 0),
		commands: make(map[string]func(Command) string),
	}
}

func (c *Context) RegisterMessage(f func(Message) string) {
	c.messages = append(c.messages, f)
}

func (c *Context) RegisterCommand(cmd string, f func(Command) string) {
	c.commands[cmd] = f
}

func (c *Context) Run(name string) {
	push, _ := push.NewSocket()
	push.AddTransport(tcp.NewTransport())
	push.Dial("tcp://127.0.0.1:5006")

	pull, _ := sub.NewSocket()
	pull.AddTransport(tcp.NewTransport())
	pull.Dial("tcp://127.0.0.1:5005")
	pull.SetOption(mangos.OptionSubscribe, []byte(""))

	for {
		var protocol [4][]byte
		bytes, _ := pull.Recv()
		msgpack.Unmarshal(bytes, &protocol)

		if string(protocol[1]) != "*" && string(protocol[1]) != name {
			continue
		}

		if string(protocol[2]) == "message" {
			var message [5][]byte
			msgpack.Unmarshal(protocol[3], &message)

			for _, f := range c.messages {
				result := f(Message{
					string(message[0]),
					string(message[1]),
					string(message[2]),
					string(message[3]),
					string(message[4]),
				})

				if result != "" {
					packed, _ := msgpack.Marshal([5]string{
						string(message[0]),
						string(message[2]),
						string(message[1]),
						result,
						string(message[4]),
					})

					output, _ := msgpack.Marshal([4]string{
						name,
						"protocol." + string(message[0]),
						"message",
						string(packed),
					})

					push.Send(output)
				}
			}
		}

		if string(protocol[2]) == "command" {
			var message [2]interface{}
			msgpack.Unmarshal(protocol[3], &message)

			var embed [5][]byte
			msgpack.Unmarshal([]byte(message[0].(string)), &embed)

			orig, _ := message[0].(string)
			line, _ := message[1].([]interface{})[0].(string)
			command := strings.SplitN(line, " ", 2)
			f := c.commands[strings.TrimPrefix(command[0], ".")]

			result := f(Command{
				strings.TrimPrefix(command[0], "."),
				command[1],
				Message{
					string(embed[0]),
					string(embed[1]),
					string(embed[2]),
					string(embed[3]),
					string(embed[4]),
				},
			})

			if result != "" {
				new_messages := message[1].([]interface{})
				new_messages = append([]interface{}{result}, new_messages[1:]...)

				packed, _ := msgpack.Marshal([2]interface{}{
					orig,
					new_messages,
				})

				output, _ := msgpack.Marshal([4]string{
					name,
					string(protocol[0]),
					"response",
					string(packed),
				})

				push.Send(output)
			}
		}
	}
}
