package models

// VersionCommand holds the information about the version command that can be used to get the version of the binary
type VersionCommand struct {
	args         []string `yaml:"args,omitempty"`
	regexVersion string   `yaml:"regexVersion,omitempty"`
}

// File holds the information about the binary files
type File struct {
	name           string         `yaml:"name,omitempty"`
	exists         bool           `yaml:"exists,omitempty"`
	version        string         `yaml:"version,omitempty"`
	versionCommand VersionCommand `yaml:"versionCommand,omitempty"`
}

// ShaInfo holds the information about the SHA checksum
// If a binary has a pre-existing checksum, it will be used
// to verify the downloaded binary using the ShaInfo.url
type ShaInfo struct {
	// url is the URL to the checksum file, if found
	url string `yaml:"url,omitempty"`

	// shaType is the type of the checksum - default should be sha256
	shaType string `yaml:"shaType,omitempty"`

	// checksum is calculated if the url is not found
	checksum string `yaml:"checksum,omitempty"`
}

// Binaries holds the information about the binaries
type Binaries struct {
	name        string  `yaml:"name,omitempty"`
	url         string  `yaml:"url,omitempty"`
	files       []File  `yaml:"files,omitempty"`
	sha         ShaInfo `yaml:"sha,omitempty"`
	description string  `yaml:"description,omitempty"`

	// shell is the shell command to run the binary, if any
	shell string `yaml:"shell,omitempty"`
}
