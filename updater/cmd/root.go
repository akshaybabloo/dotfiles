package cmd

import (
	"fmt"
	"github.com/akshaybabloo/dotfile-updater/cmd/download"
	"github.com/spf13/cobra"
)

// NewRootCmd root command
func NewRootCmd(appVersion, buildDate string) *cobra.Command {
	var rootCmd = &cobra.Command{
		Use:   "dotfiles [OPTIONS] [COMMANDS]",
		Short: "Tool to delete 'node_modules'",
		Long:  `dotfiles can be used to delete 'node_modules' recursively from sub-folders`,
	}

	rootCmd.AddCommand(download.NewDownloadCmd())

	formattedVersion := format(appVersion, buildDate)
	rootCmd.SetVersionTemplate(formattedVersion)
	rootCmd.Version = formattedVersion

	rootCmd.CompletionOptions.DisableDefaultCmd = true

	return rootCmd
}

func format(version, buildDate string) string {
	return fmt.Sprintf("dotfiles %s %s\n", version, buildDate)
}
