package main

import (
	"plugins"
	"walnut"
)

func main() {
	context := walnut.MakeContext()

	context.RegisterCommand("urban", plugins.Urban)
	context.RegisterCommand("choose", plugins.Choose)
	context.RegisterCommand("down", plugins.Choose)

	context.Run("hello2")
}
