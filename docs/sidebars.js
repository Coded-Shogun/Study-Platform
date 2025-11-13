/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'User Guide',
      items: [
        'user-guide/overview',
        'user-guide/getting-started',
        'user-guide/taking-quizzes',
        'user-guide/tracking-progress',
        'user-guide/student-levels',
      ],
    },
    {
      type: 'category',
      label: 'Admin Guide',
      items: [
        'admin-guide/overview',
        'admin-guide/managing-subjects',
        'admin-guide/managing-categories',
        'admin-guide/managing-questions',
        'admin-guide/user-management',
        'admin-guide/analytics',
      ],
    },
    {
      type: 'category',
      label: 'Developer Guide',
      items: [
        'developer-guide/setup',
        'developer-guide/architecture',
        'developer-guide/backend',
        'developer-guide/frontend',
        'developer-guide/database',
        'developer-guide/testing',
        'developer-guide/deployment',
      ],
    },
    {
      type: 'category',
      label: 'Compliance & Security',
      items: [
        'compliance/overview',
        'compliance/gdpr-compliance',
        'compliance/session-management',
        'compliance/audit-logging',
        'compliance/encryption-at-rest',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/overview',
        'api/authentication',
        'api/users',
        'api/subjects',
        'api/questions',
        'api/quiz',
        'api/progress',
        'api/compliance',
        'api/gdpr',
      ],
    },
  ],
};

export default sidebars;
