package schema

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/akshaybabloo/dotfile-updater/models"
	"github.com/invopop/jsonschema"
	"github.com/spf13/cobra"
	"github.com/stoewer/go-strcase"
)

func NewSchemaCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "schema",
		Short: "Generates JSON schema",
		RunE: func(cmd *cobra.Command, args []string) error {
			currentPath := ""
			if len(args) == 0 {
				currentPath = "."
			} else {
				currentPath = filepath.FromSlash(args[0])
			}

			r := new(jsonschema.Reflector)
			r.KeyNamer = strcase.LowerCamelCase
			binSchema := r.Reflect(&models.Binaries{})
			marshal, err := json.Marshal(binSchema)
			if err != nil {
				return err
			}
			var prettyJSON bytes.Buffer
			err = json.Indent(&prettyJSON, marshal, "", "  ")
			if err != nil {
				return err
			}
			err = os.WriteFile(filepath.Join(currentPath, "schema.json"), prettyJSON.Bytes(), 0644)
			if err != nil {
				return err
			}
			return nil
		},
	}
}
