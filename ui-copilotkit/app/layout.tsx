import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit } from "@copilotkit/react-core";

export const metadata = {
  title: "Grant Agent Lab — CopilotKit review",
  description: "CopilotKit UI for NIH R01 grant DOCX review",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit" agent="grant_reviewer">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
