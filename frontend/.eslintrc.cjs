module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  plugins: ["@typescript-eslint", "react-hooks", "react-refresh"],
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "prettier",
  ],
  ignorePatterns: ["dist", "node_modules", "src/api/schema.d.ts", "*.config.js", ".eslintrc.cjs"],
  rules: {
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true, allowExportNames: ["useToast"] },
    ],
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
  },
  overrides: [
    {
      files: ["**/*.test.tsx", "**/*.test.ts", "src/test/**"],
      rules: { "react-refresh/only-export-components": "off" },
    },
  ],
};
