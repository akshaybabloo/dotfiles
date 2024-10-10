package models

// VersionCommand holds the information about the version command that can be used to get the version of the binary
type VersionCommand struct {
	Args         string `yaml:"args,omitempty" json:"args,omitempty"`
	RegexVersion string `yaml:"regexVersion,omitempty" json:"regexVersion,omitempty"`
}

// File holds the information about the binary files
type File struct {
	Execute        bool           `yaml:"execute,omitempty" json:"execute"`
	FileName       string         `yaml:"fileName,omitempty" json:"fileName"`
	Exists         bool           `yaml:"exists,omitempty" json:"exists,omitempty"`
	VersionCommand VersionCommand `yaml:"versionCommand,omitempty" json:"versionCommand,omitempty"`
}

// ShaInfo holds the information about the SHA checksum
// If a binary has a pre-existing checksum, it will be used
// to verify the downloaded binary using the ShaInfo.url
type ShaInfo struct {
	// URL is the URL to the checksum file, if found
	URL string `yaml:"url,omitempty" json:"url,omitempty"`

	// ShaType is the type of the checksum - default should be sha256
	ShaType string `yaml:"shaType,omitempty" json:"shaType,omitempty"`

	// Checksum is calculated if the URL is not found
	Checksum string `yaml:"checksum,omitempty" json:"checksum,omitempty"`
}

// OSArch holds the information about the OS and Arch
type OSArch struct {
	// OS is the operating system
	OS string `yaml:"os,omitempty" json:"os,omitempty"`

	// Arch is the architecture
	Arch string `yaml:"arch,omitempty" json:"arch,omitempty"`
}

// Binaries holds the information about the binaries
type Binaries struct {
	Name             string  `yaml:"name,omitempty" json:"name"`
	URL              string  `yaml:"url,omitempty" json:"url"`
	Files            []File  `yaml:"files,omitempty" json:"files"`
	Sha              ShaInfo `yaml:"sha,omitempty" json:"sha,omitempty"`
	UpdatesAvailable bool    `yaml:"updatesAvailable,omitempty" json:"updatesAvailable,omitempty"`
	Description      string  `yaml:"description,omitempty" json:"description,omitempty"`
	Provider         int     `yaml:"provider,omitempty" json:"provider,omitempty"`
	OsInfo           OSArch  `yaml:"osInfo,omitempty" json:"osInfo,omitempty"`
	DownloadURL      string  `yaml:"downloadURL,omitempty" json:"downloadURL,omitempty"`
	DownloadFileName string  `yaml:"downloadFileName,omitempty" json:"downloadFileName,omitempty"`
	DownloadFolder   string  `yaml:"downloadFolder,omitempty" json:"downloadFolder,omitempty"`
	DownloadFilePath string  `yaml:"downloadPath,omitempty" json:"downloadPath,omitempty"`
	InstallLocation  string  `yaml:"installLocation" json:"installLocation"`
	CurrentVersion   string  `yaml:"currentVersion,omitempty" json:"currentVersion,omitempty"`
	NewVersion       string  `yaml:"newVersion,omitempty" json:"newVersion,omitempty"`

	// Shell is the shell command to run the binary, if any
	Shell string `yaml:"shell,omitempty" json:"shell,omitempty"`
}
