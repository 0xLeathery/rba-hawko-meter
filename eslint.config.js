const js = require("@eslint/js");
const { defineConfig } = require("eslint/config");
const globals = require("globals");

module.exports = defineConfig([
  {
    files: ["public/js/**/*.js"],
    plugins: { js },
    extends: ["js/recommended"],
    languageOptions: {
      sourceType: "script",
      globals: {
        ...globals.browser,
        Plotly: "readonly",
        Decimal: "readonly",
        countUp: "readonly",
        GaugesModule: "writable",
        ChartModule: "writable",
        DataModule: "writable",
        CountdownModule: "writable",
        CalculatorModule: "writable",
        InterpretationsModule: "writable",
        SparklineModule: "writable",
      },
    },
    rules: {
      "max-len": ["error", { code: 88 }],
      "no-redeclare": [
        "error",
        { builtinGlobals: false },
      ],
      "no-unused-vars": [
        "error",
        {
          varsIgnorePattern:
            "^(GaugesModule|ChartModule|DataModule"
            + "|CountdownModule|CalculatorModule"
            + "|InterpretationsModule|SparklineModule)$",
          caughtErrorsIgnorePattern: "^_",
          argsIgnorePattern: "^_",
        },
      ],
    },
  },
]);
