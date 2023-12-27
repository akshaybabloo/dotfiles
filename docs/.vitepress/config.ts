import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Dotfiles",
  description: "Helpful Dotfiles",
  head: [['link', { rel: 'icon', href: '/favicon.ico' }]],
  srcExclude: ['**/README.md'],
  themeConfig: {
    search: {
      provider: 'local'
    },
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Install', link: '/install' },
      { text: 'Functions', link: '/functions' },
      { text: 'Aliases', link: '/aliases' },
    ],
    logo: '/logo.svg',

    sidebar: [
    ],

    outline: {
      level: "deep",
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/akshaybabloo/dotfiles' }
    ],

    footer: {
      message: `Made with ❤️ by <a href='https://gollahalli.com'>Akshay Raj Gollahalli</a>`,
    }
  },
  sitemap: {
    hostname: 'https://dotfiles.gollahalli.com',
    transformItems: (items) => {
      items = items.filter((item) => !item.url.includes('auto'));
      return items;
    }
  },
})
