import type { Preview } from "@storybook/react";
import "../src/app/globals.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: "dark",
      values: [
        {
          name: "dark",
          value: "rgb(13 17 23)",
        },
        {
          name: "light",
          value: "rgb(248 250 252)",
        },
      ],
    },
  },
};

export default preview;
