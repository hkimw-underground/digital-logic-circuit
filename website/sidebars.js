/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: '개념 이해하기',
      collapsed: false,
      items: [
        'system_docs/EASY_GUIDE',
        'system_docs/architecture_mindmap',
      ],
    },
    {
      type: 'category',
      label: '시스템 설계',
      collapsed: false,
      items: [
        'system_docs/system_design',
        'system_docs/hardware_spec',
        'system_docs/arduino_setup',
      ],
    },
    {
      type: 'category',
      label: '코드 구조',
      items: [
        'code_docs/server_modules',
        'code_docs/arduino_modules',
      ],
    },
    {
      type: 'category',
      label: '보안',
      items: [
        'SECURITY_ANALYSIS',
        'SECURITY_REPORT',
      ],
    },
    {
      type: 'category',
      label: '개발 스토리',
      items: [
        'history/vibe_coding_journey',
        'history/security_fix_case',
        'history/hardware_integration',
      ],
    },
    {
      type: 'category',
      label: '프로젝트 운영',
      items: [
        'system_docs/DEVELOPMENT_PLAN',
        'system_docs/REVIEW',
      ],
    },
    {
      type: 'category',
      label: '부록',
      collapsed: true,
      items: [
        'TROUBLESHOOTING',
        'system_docs/DEPLOYMENT',
        'system_docs/models/README',
        'system_docs/latex_tikz_source',
        'system_docs/PRESENTATION_GUIDE',
        'vibe_prompts/main_prompt',
        'vibe_prompts/sub_prompts/joint_development',
        'vibe_prompts/sub_prompts/arduino_dev',
        'vibe_prompts/sub_prompts/python_opt',
        'vibe_prompts/sub_prompts/beta_test',
      ],
    },
  ],
};

export default sidebars;
