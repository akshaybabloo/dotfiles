// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://dotfiles.gollahalli.com',
	integrations: [
		starlight({
			title: 'Dotfiles',
			favicon: '/favicon.ico',
			lastUpdated: true,
			description: 'A collection of my dotfiles and scripts.',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/akshaybabloo/dotfiles' }],
			sidebar: [
				{
					label: 'Reference',
					items: [{ autogenerate: { directory: 'reference' } }],
				},
			],
			logo: {
				src: './src/assets/logo.svg',
				alt: 'Dotfiles Logo'
			},
			components: {
				Footer: './src/components/Footer.astro',
			},
		}),
	],
});
