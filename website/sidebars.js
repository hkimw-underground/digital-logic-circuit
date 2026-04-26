/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: '우리는 이렇게 개발했다',
      items: [
        'history/vibe_coding_journey',
        'history/security_fix_case',
        'history/hardware_integration',
      ],
    },
    {
      type: 'category',
      label: '시스템 문서',
      items: [
        'system_docs/system_design',
        'system_docs/hardware_spec',
        'system_docs/arduino_setup',
        'system_docs/EASY_GUIDE',
        'system_docs/architecture_mindmap',
        'system_docs/latex_tikz_source',
        'SECURITY_ANALYSIS',
        'TROUBLESHOOTING',
      ],
    },
    {
      type: 'category',
      label: '개발 가이드',
      items: [
        'system_docs/DEVELOPMENT_PLAN',
        'system_docs/PRESENTATION_GUIDE',
      ],
    },
    {
      type: 'category',
      label: '코드 모듈 가이드',
      items: [
        'code_docs/server_modules',
        'code_docs/arduino_modules',
      ],
    },
    {
      type: 'category',
      label: '바이브 코딩 프롬프트',
      items: [
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
