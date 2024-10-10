package download

import (
	"github.com/MakeNowJust/heredoc"
	"github.com/briandowns/spinner"
	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"time"
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

			s := spinner.New(spinner.CharSets[11], 100*time.Millisecond)
			s.Suffix = color.GreenString(" Checking for updates...")
			s.Start()
			// TODO: something
			time.Sleep(2 * time.Second)
			s.Suffix = color.GreenString(" Downloading updates...")
			time.Sleep(2 * time.Second)
			s.Stop()

			return nil
		},
	}

	deleteCmd.Flags().BoolVar(&isCheckOnly, "check", false, "Check for updates")
	deleteCmd.Flags().BoolVar(&nqa, "nqa", false, "Update without asking")

	return deleteCmd
}
