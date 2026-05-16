import type { AppProps } from "next/app";
import { appWithTranslation } from "next-i18next";
import AppChrome from "../components/AppChrome";
import { AuthProvider } from "../context/AuthContext";
import "../styles/globals.css";

function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <div className="dark">
        <AppChrome>
          <Component {...pageProps} />
        </AppChrome>
      </div>
    </AuthProvider>
  );
}

export default appWithTranslation(App);

