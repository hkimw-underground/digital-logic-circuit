// @ts-check

import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: '2FA Smart Door Lock System',
  tagline: 'Technical Report for 2-Factor Authentication Door Lock System',
  favicon: 'img/favicon.ico',

  url: 'https://school-project-hwkim-dev.github.io',
  baseUrl: '/digital-logic-circuit/',

  organizationName: 'school-project-hwkim-dev',
  projectName: 'digital-logic-circuit',

  onBrokenLinks: 'throw',

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: 'docs',
        },
        blog: false, // Disable blog for technical report
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'light',
        disableSwitch: true, // Force light mode for technical report style
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: '2FA Smart Door Lock',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Technical Report',
          },
          {to: '/dashboard', label: 'Validation Status', position: 'left'},
          {
            href: 'https://github.com/school-project-hwkim-dev/digital-logic-circuit',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              {
                label: 'Executive Summary',
                to: '/docs/executive-summary',
              },
              {
                label: 'System Architecture',
                to: '/docs/architecture',
              },
              {
                label: 'Validation',
                to: '/docs/validation/test-plan',
              },
            ],
          },
          {
            title: 'Repository',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/school-project-hwkim-dev/digital-logic-circuit',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} 2FA Smart Door Lock Project.`,
      },
      prism: {
        theme: prismThemes.github,
      },
      mermaid: {
        theme: {light: 'default', dark: 'dark'},
      },
    }),
};

export default config;
