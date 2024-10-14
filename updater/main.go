package main

import (
	"fmt"
	"github.com/akshaybabloo/dotfile-updater/cmd"
	"os"
)

var (
	version   = "dev"
	buildDate = ""
)

func main() {
	rootCmd := cmd.NewRootCmd(version, buildDate)
	err := rootCmd.Execute()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
