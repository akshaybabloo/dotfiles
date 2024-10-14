package download

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/MakeNowJust/heredoc"
	"github.com/akshaybabloo/dotfile-updater/models"
	"github.com/akshaybabloo/dotfile-updater/pkg/io"
	"github.com/akshaybabloo/dotfile-updater/pkg/net"
	"github.com/briandowns/spinner"
	"github.com/fatih/color"
	"github.com/jedib0t/go-pretty/v6/table"
	"github.com/spf13/cobra"
)

var isCheckOnly bool
var nqa bool

// NewDownloadCmd command function to downloads required binaries
func NewDownloadCmd() *cobra.Command {
	var deleteCmd = &cobra.Command{
		Use:   "download",
		Short: "Download required binaries",
		Example: heredoc.Doc(`
			To check and download all the required binaries
			$ dotfiles download <config files folder>

			To only check for updates
			$ dotfiles download <config files folder> --check

			To update without asking
			$ dotfiles download <config files folder> --nqa`),
		RunE: func(cmd *cobra.Command, args []string) error {

			if len(args) == 0 {
				return errors.New("no config files folder provided")
			}

			s := spinner.New(spinner.CharSets[11], 100*time.Millisecond)
			s.Suffix = color.GreenString(" Checking for updates...")
			s.Start()

			stat, err := os.Stat(args[0])
			if err != nil {
				return err
			}
			if !stat.IsDir() {
				return errors.New("provided path is not a directory")
			}

			data, err := io.ReadYamlFiles(filepath.FromSlash(args[0]))
			if err != nil {
				return err
			}

			var bins []models.Binaries
			for binaries, err := range data {
				if err != nil {
					return err
				}

				updates, err := net.CheckUpdates(binaries)
				if err != nil {
					return err
				}

				bins = append(bins, updates)
			}

			var binUpdates []models.Binaries
			for _, bin := range bins {
				if bin.UpdatesAvailable {
					binUpdates = append(binUpdates, bin)
				}
			}

			if len(binUpdates) == 0 {
				s.Stop()
				fmt.Println(color.GreenString("No updates available"))
				return nil
			}
			s.FinalMSG = color.GreenString("Updates available\n")
			s.Stop()

			t := table.NewWriter()
			t.SetOutputMirror(os.Stdout)
			t.AppendHeader(table.Row{"Name", "Current Version", "New Version"})
			for _, update := range binUpdates {
				t.AppendRow([]interface{}{update.Name, update.CurrentVersion, update.NewVersion})
			}
			t.SetStyle(table.StyleLight)
			t.Render()

			if isCheckOnly {
				return nil
			}

			if !nqa {
				fmt.Print("Do you want to update? (y/n): ")
				var input string
				_, err := fmt.Scanln(&input)
				if err != nil {
					return err
				}
				if input != "y" {
					return nil
				}
			}

			s = spinner.New(spinner.CharSets[11], 100*time.Millisecond)
			s.Suffix = color.GreenString(" Installing updates...")
			s.Start()

			for _, update := range binUpdates {
				err = net.DownloadAndMoveFiles(update)
				if err != nil {
					return err
				}
			}
			s.FinalMSG = color.GreenString("Updates installed\n")
			s.Stop()

			return nil
		},
	}

	deleteCmd.Flags().BoolVar(&isCheckOnly, "check", false, "Check for updates")
	deleteCmd.Flags().BoolVar(&nqa, "nqa", false, "Update without asking")

	return deleteCmd
}
