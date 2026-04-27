/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    'executive-summary',
    'problem-objective',
    'architecture',
    'authentication-flow',
    {
      type: 'category',
      label: 'Operation and Usage',
      items: [
        'operation/setup',
        'operation/user-guide',
      ],
    },
    {
      type: 'category',
      label: 'Hardware Implementation',
      items: [
        'hardware/hardware-overview',
        'hardware/wiring',
      ],
    },
    {
      type: 'category',
      label: 'Software System',
      items: [
        'software/backend',
        'software/database',
        'software/serial-protocol',
      ],
    },
    {
      type: 'category',
      label: 'Security',
      items: [
        'security/threat-model',
      ],
    },
    {
      type: 'category',
      label: 'Validation',
      items: [
        'validation/test-plan',
        'validation/limitations',
      ],
    },
    {
      type: 'category',
      label: 'Appendix',
      items: [
        'appendix/development-notes',
        'appendix/ai-assisted-workflow',
      ],
    },
  ],
};

export default sidebars;
