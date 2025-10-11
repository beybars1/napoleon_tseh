import type { AppProps } from 'next/app';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { store } from '@/redux/store';
import theme from '@/styles/theme';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

const queryClient = new QueryClient();

const publicPaths = ['/login'];

export default function App({ Component, pageProps, router }: AppProps) {
  const isPublicPath = publicPaths.includes(router.pathname);

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          {isPublicPath ? (
            <Component {...pageProps} />
          ) : (
            <ProtectedRoute>
              <Component {...pageProps} />
            </ProtectedRoute>
          )}
        </ThemeProvider>
      </QueryClientProvider>
    </Provider>
  );
}
