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
    ],
    logo: '/logo.svg',

    sidebar: [
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/akshaybabloo/dotfiles' }
    ]
  }
})
