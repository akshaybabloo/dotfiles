// Package models implements the models for the Version Control Providers
package models

// GitHubInfo holds the information about the GitHub URL
type GitHubInfo struct {
	// Owner is the owner of the repository
	Owner string `yaml:"owner,omitempty" json:"owner,omitempty"`

	// Repo is the repository name related to it's Owner
	Repo string `yaml:"repo,omitempty" json:"repo,omitempty"`
}
