import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
export default [{ignores:['dist','coverage','node_modules']},{files:['**/*.{js,jsx}'],languageOptions:{ecmaVersion:'latest',sourceType:'module',globals:{...globals.browser,...globals.node},parserOptions:{ecmaFeatures:{jsx:true}}},plugins:{react,'react-hooks':reactHooks,'react-refresh':reactRefresh},settings:{react:{version:'detect'}},rules:{...js.configs.recommended.rules,...react.configs.recommended.rules,...reactHooks.configs.recommended.rules,'react/react-in-jsx-scope':'off','react/jsx-uses-vars':'error','react/prop-types':'off','no-unused-vars':['error',{argsIgnorePattern:'^_',varsIgnorePattern:'^[A-Z_]'}],'react-refresh/only-export-components':['warn',{allowConstantExport:true}]}}];
