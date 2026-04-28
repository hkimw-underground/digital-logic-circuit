// @ts-check

import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: '2FA 스마트 도어락 시스템',
  tagline: '2단계 인증 도어락 시스템 기술 보고서',
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
    defaultLocale: 'ko',
    locales: ['ko'],
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
        title: '2FA 스마트 도어락',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: '기술 보고서',
          },
          {to: '/dashboard', label: '검증 상태', position: 'left'},
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
            title: '문서',
            items: [
              {
                label: '요약 보고서',
                to: '/docs/executive-summary',
              },
              {
                label: '시스템 아키텍처',
                to: '/docs/architecture',
              },
              {
                label: '검증',
                to: '/docs/validation/test-plan',
              },
            ],
          },
          {
            title: '저장소',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/school-project-hwkim-dev/digital-logic-circuit',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} 2FA 스마트 도어락 프로젝트.`,
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
