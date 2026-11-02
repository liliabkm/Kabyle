import type { Metadata } from "next";
import "./globals.css";
import "./playful.css";
export const metadata: Metadata = {
  title: "Tifin · Un premier pas en kabyle",
  description:
    "Découvrez les lettres tifinaghes, pratiquez et retrouvez vos progrès.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
