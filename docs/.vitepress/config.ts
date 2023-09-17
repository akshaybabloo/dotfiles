import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Dotfiles",
  description: "Helpful Dotfiles",
  base: '/dotfiles/',
  themeConfig: {
    search: {
      provider: 'local'
    },
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Get Started', link: '/get-started' },
      { text: 'Functions', link: '/functions' },
      { text: 'Aliases', link: '/aliases' },
    ],
    logo: '/logo.svg',

    sidebar: [
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/akshaybabloo/dotfiles' }
    ]
  }
})
